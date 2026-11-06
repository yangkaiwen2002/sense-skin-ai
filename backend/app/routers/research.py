from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, Field, PositiveInt
from sqlalchemy import update
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.limiter import limiter
from app.models import Item, ResearchSession, ResearchRun
from app.services.research_model import model_status
from app.services.research_service import execute_run, serialize_run, utc, frame
from data_sources.item_catalog import MARKET_NAMES

router = APIRouter(prefix="/research", tags=["research"])


class CreateSession(BaseModel):
    title: str = Field(default="新的饰品研究", min_length=1, max_length=160)


class StartRun(BaseModel):
    request_id: UUID
    question: str = Field(min_length=1, max_length=2000)
    item_ids: list[PositiveInt] | None = Field(default=None, max_length=3)
    mode: Literal["market", "compare", "rental", "knowledge"] = "market"
    refresh: bool = True
    days: int = Field(default=7, ge=1, le=365)
    budget: float = Field(default=1000, ge=0, le=1e9, allow_inf_nan=False)


def session_summary(row):
    return {"id": row.id, "title": row.title, "item_ids": row.item_ids,
            "active_run_id": row.active_run_id, "updated_at": utc(row.updated_at)}


def get_session(db, session_id):
    row = db.get(ResearchSession, str(session_id))
    if not row:
        raise HTTPException(404, "研究会话不存在")
    # Expire a lease left by a killed worker; active runs have a 240s deadline.
    if row.active_run_id and row.updated_at < datetime.utcnow() - timedelta(minutes=10):
        old = db.get(ResearchRun, row.active_run_id)
        if old and old.status == "running":
            old.status, old.error = "interrupted", "服务重启或连接中断，请重新发起研究。"
            old.steps = [{**s, "status": "interrupted", "summary": old.error} if s["status"] == "running" else s for s in old.steps]
        row.active_run_id = None
        db.commit()
    return row


@router.get("/status")
def status():
    return {"model": model_status(), "sources": [
        {"id": "steam", "label": "Steam 行情", "status": "available", "detail": f"按精确名称采集，已映射 {len(MARKET_NAMES)} 件目录饰品；可用性取决于来源响应。"},
        {"id": "news", "label": "CS2 官方公告", "status": "available", "detail": "Steam 官方新闻；公告影响仍待评估。"},
        {"id": "buff", "label": "BUFF 行情", "status": "configured" if settings.BUFF_COOKIE and settings.BUFF_GOODS_IDS else "not_configured", "detail": "需要账户凭据与精确商品映射。"},
        {"id": "rental", "label": "租赁报价", "status": "demo", "detail": "尚未接入真实租赁报价。"},
        {"id": "knowledge", "label": "研究知识库", "status": "available", "detail": "静态资料；检索结果中的历史价格不代表当前行情。"},
    ]}


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db)):
    rows = db.query(ResearchSession).order_by(ResearchSession.updated_at.desc()).limit(50).all()
    return {"sessions": [session_summary(row) for row in rows]}


@router.post("/sessions", status_code=201)
def create_session(req: CreateSession, db: Session = Depends(get_db)):
    title = req.title.strip()
    if not title:
        raise HTTPException(422, "研究标题不能为空")
    row = ResearchSession(id=str(uuid4()), title=title, item_ids=[])
    db.add(row); db.commit(); db.refresh(row)
    return session_summary(row)


@router.get("/sessions/{session_id}")
def session_detail(session_id: UUID, db: Session = Depends(get_db)):
    row = get_session(db, session_id)
    runs = db.query(ResearchRun).filter(ResearchRun.session_id == row.id).order_by(ResearchRun.created_at).all()
    return {**session_summary(row), "runs": [serialize_run(run) for run in runs]}


@router.post("/sessions/{session_id}/runs")
@limiter.limit("10/5minute")
def start_run(request: Request, session_id: UUID, req: StartRun, db: Session = Depends(get_db)):
    question = req.question.strip()
    if not question:
        raise HTTPException(422, "请输入研究问题")
    row = get_session(db, session_id)
    existing = db.query(ResearchRun).filter_by(session_id=row.id, request_id=str(req.request_id)).first()
    if existing:
        if existing.status == "running":
            raise HTTPException(409, "这次研究正在运行，可刷新会话查看进度。")
        return StreamingResponse(iter([frame({"type": "completed", "run": serialize_run(existing)}), "data: [DONE]\n\n"]), media_type="text/event-stream")
    ids = list(dict.fromkeys(req.item_ids if req.item_ids is not None else row.item_ids))
    if req.mode != "knowledge" and not ids:
        raise HTTPException(422, "请选择至少一件饰品，或切换到知识问答。")
    if ids and db.query(Item.id).filter(Item.id.in_(ids)).count() != len(ids):
        raise HTTPException(422, "所选饰品不存在，请重新选择。")
    run_id = str(uuid4())
    # Atomic reservation also prevents concurrent runs across worker processes.
    claimed = db.execute(update(ResearchSession).where(ResearchSession.id == row.id,
        ResearchSession.active_run_id.is_(None)).values(active_run_id=run_id, updated_at=datetime.utcnow()))
    if not claimed.rowcount:
        db.rollback()
        raise HTTPException(409, "本会话已有研究进行中，请等待完成。")
    row.item_ids = ids
    if row.title == "新的饰品研究":
        row.title = question[:80]
    run = ResearchRun(id=run_id, session_id=row.id, request_id=str(req.request_id),
        question=question, item_ids=ids, parameters=req.model_dump(include={"mode", "refresh", "days", "budget"}),
        status="running", steps=[], sources=[], answer="")
    db.add(run); db.commit()
    return StreamingResponse(execute_run(db.get_bind(), run.id, req.model_dump()), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/runs/{run_id}/artifact")
def artifact(run_id: UUID, db: Session = Depends(get_db)):
    run = db.get(ResearchRun, str(run_id))
    if not run or not run.artifact or run.status != "completed":
        raise HTTPException(404, "研究产物尚未生成")
    return Response(run.artifact["text"], media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="senseskin-research-{run.id}.md"'})
