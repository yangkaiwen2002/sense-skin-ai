"""AI chat streaming endpoint for SkinSense."""
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.limiter import limiter
from app.models.item import Item
from app.services.analytics_service import get_item_overview
from app.services.scoring import score_item
from app.services.event_ingestion import get_active_events
from app.services.event_mapper import map_events_to_item
from app.services.decision_engine import decide

router = APIRouter(prefix="/items", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def _build_system(item: Item, overview, decision=None, event_map=None) -> str:
    best = overview.platforms[0] if overview and overview.platforms else None

    price_lines = []
    if best:
        if best.current_price:
            price_lines.append(f"- 当前价格 ({best.platform}): ¥{best.current_price:.2f}")
        if best.avg_7d:
            price_lines.append(f"- 7日均价: ¥{best.avg_7d:.2f}")
        if best.avg_30d:
            price_lines.append(f"- 30日均价: ¥{best.avg_30d:.2f}")
        if best.return_7d is not None:
            price_lines.append(f"- 7日涨跌: {best.return_7d*100:+.1f}%")
        if best.liquidity_score is not None:
            price_lines.append(f"- 流动性评分: {best.liquidity_score:.0f}/100")
        if best.volatility_7d is not None:
            price_lines.append(f"- 价格波动率: {best.volatility_7d:.4f}")
        if best.risk_labels:
            price_lines.append(f"- 风险标签: {', '.join(best.risk_labels)}")

    all_platforms = []
    if overview:
        for p in overview.platforms:
            if p.current_price:
                all_platforms.append(f"  • {p.platform}: ¥{p.current_price:.2f}")

    price_section = "\n".join(price_lines) if price_lines else "暂无价格数据"
    platform_section = "\n".join(all_platforms) if all_platforms else "暂无跨平台数据"

    # Decision engine section
    decision_section = ""
    if decision:
        rec_cn = decision.recommendation_cn
        rec    = decision.recommendation
        conf   = int(decision.confidence * 100)
        rationale = decision.rationale
        upsides   = "\n".join(f"  ✓ {u}" for u in decision.upside_factors[:3])
        risks_txt = "\n".join(f"  ✗ {r}" for r in decision.risk_factors[:3])
        ss = decision.score_summary
        signals_txt = "\n".join(
            f"  [{s['direction']}] {s['label']}: {s['note']}"
            for s in decision.supporting_signals[:6]
        )
        decision_section = f"""
━━━ AI 决策引擎输出 ━━━
推荐操作: {rec_cn} ({rec}) | 置信度: {conf}%
核心判断: {rationale}

综合评分: {ss.get('total', 'N/A')}/100
评分维度: 稀有度{ss.get('rarity','?')} | 外观{ss.get('exterior','?')} | 流动性{ss.get('liquidity','?')} | 趋势{ss.get('trend','?')} | 估值{ss.get('valuation','?')} | 需求{ss.get('demand','?')} | 事件{ss.get('event','?')}
估值标签: {ss.get('valuation_label','合理')} | 净信号: {ss.get('net_signal', 0):+.1f}

做多因素:
{upsides or "  暂无明显利好"}

风险因素:
{risks_txt or "  暂无明显风险"}

证据链 (决策依据):
{signals_txt}"""

    # Event context section
    event_section = ""
    if event_map and event_map.relevant_events:
        lines = []
        for e in event_map.relevant_events[:4]:
            direction_icon = "▲" if e.impact_direction == "positive" else ("▼" if e.impact_direction == "negative" else "◆")
            lines.append(f"  {direction_icon} {e.title} ({e.window_label}) — 影响强度 {e.impact_strength:.0%}")
        event_section = f"""
━━━ 市场事件信号 ━━━
综合事件影响: {event_map.event_impact_score:+.2f} | 事件评分: {event_map.event_signal_score}/100
摘要: {event_map.event_summary}

相关事件:
""" + "\n".join(lines)

    return f"""你是 SkinSense AI，一个专业的 CS2（反恐精英2）饰品市场分析助手。你由结构化的市场信号驱动，不依赖猜测。你的回答必须基于下方提供的数据。

━━━ 当前分析饰品 ━━━
名称: {item.item_name}
武器: {item.weapon_type or "未知"} | 皮肤: {item.skin_name or "未知"}
稀有度: {item.rarity or "未知"} | 磨损: {item.exterior or "未知"}
StatTrak: {"是" if item.stattrak else "否"} | 纪念品: {"是" if item.souvenir else "否"}

━━━ 实时市场数据 ━━━
{price_section}

跨平台价格对比:
{platform_section}
{decision_section}
{event_section}

━━━ 你的职责 ━━━
以上数据来自真实的结构化信号管道（价格数据库 + 事件管道 + 多维度 AI 评分模型）。
基于这些数据，回答用户关于此饰品的问题：
- 买入/卖出/持有建议（必须引用决策引擎输出）
- 事件催化分析（引用具体事件）
- 估值合理性分析
- 同类饰品对比
- 风险提示

重要原则：
1. 凡涉及"值不值得买"，必须明确引用决策引擎的推荐结果和置信度
2. 凡提到市场信号，必须具体说明是哪个事件（不要泛泛而谈）
3. 如果估值偏高，必须说明；不要用模糊语言回避
4. 用中文回答，除非用户用英文。简洁有力，给出可操作建议。"""


@router.post("/{item_id}/chat")
@limiter.limit("30/5minute")
def chat_stream(request: Request, item_id: int, req: ChatRequest, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    overview = get_item_overview(db, item_id)

    api_key = settings.CLAUDE_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Claude API key not configured")

    # Run the full decision pipeline to ground Claude's answers
    try:
        events    = get_active_events(days=90)
        event_map = map_events_to_item(item, events)
        score     = score_item(db, item_id, event_map=event_map)
        decision  = decide(item, score, event_map) if score else None
    except Exception:
        decision  = None
        event_map = None

    system_prompt = _build_system(item, overview, decision=decision, event_map=event_map)
    messages = [{"role": m["role"], "content": m["content"]} for m in req.history]
    messages.append({"role": "user", "content": req.message})

    def generate():
        try:
            client = anthropic.Anthropic(api_key=api_key)
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
