"""A persisted, bounded research workflow over real application tools."""
import asyncio
import copy
import json
import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import ResearchSession, ResearchRun
from app.services import research_model
from app.services.analytics_service import get_item_overview
from app.services.comparison_service import get_comparison
from app.services.rental_service import rent_vs_buy
from app.services.price_fetcher import refresh_item_prices
from app.services.news_ingestion import refresh_news, get_news
from app.schemas.rental import RentVsBuyRequest
from app.rag.retriever import get_retriever


def utc(value):
    return value.isoformat() + "Z" if value else None


def serialize_run(run):
    return {"id": run.id, "session_id": run.session_id, "request_id": run.request_id,
            "question": run.question, "item_ids": run.item_ids, "status": run.status,
            "parameters": run.parameters,
            "answer_mode": run.answer_mode, "steps": run.steps, "sources": run.sources,
            "answer": run.answer, "error": run.error, "artifact": run.artifact,
            "created_at": utc(run.created_at)}


def frame(event):
    return "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"


def record_artifact(run):
    title = run.question[:80]
    text = f"# {title}\n\n生成时间：{utc(datetime.utcnow())}\n模式：{'AI 综合研究' if run.answer_mode == 'generated' else '证据整理（未调用模型）'}\n\n{run.answer}\n\n## 本轮来源\n"
    for source in run.sources:
        text += f"\n### [{source['id']}] {source['title']}\n{source['summary']}\n"
        if source.get("url"):
            text += source["url"] + "\n"
    return {"title": title, "text": text, "format": "markdown"}


def evidence_summary(sources):
    lines = ["本次已完成数据与证据整理，尚未调用模型生成综合结论。"]
    if not sources:
        lines.append("本轮没有可用证据，请选择饰品或更换问题后重试。")
    for source in sources:
        if source["kind"] in ("market", "rental"):
            lines.append(f"[{source['id']}] {source['title']}：{source['summary']}")
    knowledge = [s for s in sources if s["kind"] == "knowledge"]
    news = [s for s in sources if s["kind"] == "news"]
    lines.append(f"找到 {len(knowledge)} 条知识资料与 {len(news)} 条官方公告，可展开来源核对原文。公告对饰品的价格影响仍待评估。")
    lines.append("演示、未核验或过期报价不代表实时可成交价格；历史不足时无法判断价格趋势。")
    return "\n\n".join(lines)


async def execute_run(bind, run_id, options):
    # Own the session for the entire stream (FastAPI dependency teardown can
    # precede StreamingResponse on versions before 0.118).
    with Session(bind=bind, expire_on_commit=False) as db:
        run = db.get(ResearchRun, run_id)
        session = db.get(ResearchSession, run.session_id)
        steps, sources = [], []

        def save():
            run.steps, run.sources = copy.deepcopy(steps), copy.deepcopy(sources)
            run.updated_at = session.updated_at = datetime.utcnow()
            db.commit()

        def add_source(kind, title, summary, data=None, url=None):
            source = {"id": f"S{len(sources)+1}", "kind": kind, "title": title,
                      "summary": summary, "data": data, "url": url}
            sources.append(source)

        async def step(name, call):
            entry = {"id": f"step-{len(steps)+1}", "label": name, "status": "running", "summary": ""}
            steps.append(entry)
            save()
            yield {"type": "step", "step": dict(entry)}
            started = time.monotonic()
            try:
                summary, ok = await call()
                entry.update(status="done" if ok else "warning", summary=summary)
            except asyncio.CancelledError:
                entry.update(status="cancelled", summary="执行已停止")
                raise
            except Exception:
                entry.update(status="error", summary="此数据源暂时不可用，已保留其他证据。")
                db.rollback()
            entry["duration_ms"] = round((time.monotonic() - started) * 1000)
            save()
            yield {"type": "step", "step": dict(entry)}
            yield {"type": "sources", "sources": list(sources)}

        async def update_prices():
            # A bounded selected-item refresh, never the whole catalog.
            needed = []
            for item_id in run.item_ids:
                overview = get_item_overview(db, item_id)
                recent = any(p.price_kind == "observed" and p.snapshot_time and
                    datetime.utcnow() - p.snapshot_time < timedelta(minutes=5) for p in overview.platforms)
                if not recent:
                    needed.append(item_id)
            if not needed:
                return "所选饰品已有 5 分钟内的真实采集快照。", True
            result = await refresh_item_prices(db, needed)
            ok = result.get("status") == "success"
            return result.get("message") or f"真实采集 {result.get('fetched', 0)} 条；失败 {result.get('failed', 0)}；未映射 {result.get('skipped', 0)}。", ok

        async def read_market():
            for item_id in run.item_ids:
                overview = get_item_overview(db, item_id)
                comparison = get_comparison(db, item_id)
                rows = []
                for p in overview.platforms:
                    kind = {"observed": "采集报价", "demo": "演示数据"}.get(p.price_kind, "来源未核验")
                    price = f"¥{p.current_price:,.2f}" if p.current_price is not None else "暂无价格"
                    stamp = p.snapshot_time.strftime("%Y-%m-%d %H:%M UTC") if p.snapshot_time else "采集时间未知"
                    rows.append(f"{p.platform} {price} · {kind}{' · 已过期' if p.is_stale else ''} · {stamp}")
                fresh_observed = [p for p in overview.platforms if p.price_kind == "observed" and not p.is_stale and p.current_price]
                if len(fresh_observed) < 2:
                    rows.append("不足两个平台的新鲜真实报价，暂不能验证跨平台价差")
                data = {"overview": overview.model_dump(mode="json"), "comparison": comparison.model_dump(mode="json")}
                add_source("market", overview.item_name, "；".join(rows) or "暂无报价", data, f"/item/{item_id}")
            return f"已核对 {len(run.item_ids)} 件饰品的平台、来源、时间与价差。", True

        async def read_rental():
            for item_id in run.item_ids:
                result = rent_vs_buy(db, item_id, RentVsBuyRequest(days=options["days"], budget=options["budget"]))
                if result:
                    add_source("rental", result.item_name + " · 租买方案", result.explanation, result.model_dump(mode="json"), f"/rent-vs-buy?item={item_id}")
            return "已按使用天数、预算和现有租金计算；租赁报价仍为演示数据。", True

        async def read_news():
            news = get_news(db)
            if options["refresh"] and (not news or datetime.utcnow() - datetime.fromisoformat(news[0]["fetched_at"].rstrip("Z")) > timedelta(minutes=15)):
                result = await refresh_news(db)
                news = get_news(db)
                synced = result.get("status") == "success"
            else:
                synced = True
            for event in news[:4]:
                add_source("news", event["title"], event["summary"][:1200],
                           {"published_at": event["event_date"], "fetched_at": event["fetched_at"], "impact": "待评估"}, event["source_url"])
            return f"载入 {min(len(news), 4)} 条官方公告；属于全局背景，影响待评估。" + (" 同步失败，保留已有内容。" if not synced else ""), synced

        async def search_knowledge():
            scope = " ".join(s["title"] for s in sources if s["kind"] == "market")
            search = get_retriever().search(f"{run.question} {scope}".strip(), top_k=3)
            for item in search["results"]:
                add_source("knowledge", item["title"], item["content"][:1800], {"category": item["category"], "type": "静态知识，不代表当前行情"})
            return f"检索到 {len(search['results'])} 条知识资料，已保留原文。", True

        try:
            yield frame({"type": "run", "run": serialize_run(run)})
            async with asyncio.timeout(240):
                jobs = []
                if run.item_ids:
                    if options["refresh"]:
                        jobs.append(("更新所选饰品真实报价", update_prices))
                    jobs.append(("核对平台行情与来源", read_market))
                    if options["mode"] == "rental":
                        jobs.append(("计算租赁与购买方案", read_rental))
                jobs.extend([("读取 CS2 官方公告", read_news), ("检索研究知识库", search_knowledge)])
                for label, call in jobs:
                    async for event in step(label, call):
                        yield frame(event)
                if research_model.model_status()["configured"]:
                    run.answer_mode = "generated"
                    entry = {"id": "synthesis", "label": "基于本轮证据生成研究", "status": "running", "summary": ""}
                    steps.append(entry)
                    save()
                    yield frame({"type": "step", "step": dict(entry)})
                    history = []
                    previous = db.query(ResearchRun).filter(ResearchRun.session_id == session.id,
                        ResearchRun.id != run.id, ResearchRun.status == "completed").order_by(ResearchRun.created_at.desc()).limit(4).all()
                    for old in reversed(previous):
                        history.extend([{"role": "user", "content": old.question}, {"role": "assistant", "content": old.answer[:4000]}])
                    async for chunk in research_model.stream_answer(run.question, sources, history):
                        run.answer += chunk
                        yield frame({"type": "text", "text": chunk})
                    if not run.answer.strip():
                        raise RuntimeError("模型未返回内容")
                    entry.update(status="done", summary="研究结论已生成，可按来源编号核对。")
                    yield frame({"type": "step", "step": dict(entry)})
                else:
                    run.answer = evidence_summary(sources)
                    yield frame({"type": "notice", "text": "当前为证据工作流；模型尚未连接，未生成 AI 结论。"})
                    yield frame({"type": "text", "text": run.answer})
                run.status = "completed"
                run.artifact = record_artifact(run)
        except (asyncio.CancelledError, GeneratorExit):
            run.status, run.error = "cancelled", "研究已停止，已完成的证据已保留。"
            raise
        except Exception:
            run.status, run.error = "failed", "研究未完整完成，已保留工具结果和已收到的内容。请检查服务连接后重试。"
            yield frame({"type": "error", "error": run.error})
        finally:
            for entry in steps:
                if entry["status"] == "running":
                    entry.update(status=run.status, summary=run.error or "执行中断")
            if session.active_run_id == run.id:
                session.active_run_id = None
            save()
        yield frame({"type": "completed", "run": serialize_run(run)})
        yield "data: [DONE]\n\n"
