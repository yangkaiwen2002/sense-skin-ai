"""Local workspace diagnostics; no credentials or arbitrary upstream URLs exposed."""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import httpx
from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.models import ResearchRun, Item, PriceSnapshot
from app.services.research_model import model_status
from app.rag.retriever import get_retriever
from app.rag.evaluation import evaluate, BACKEND

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.get("/status")
async def status(db: Session = Depends(get_db)):
    model = model_status()
    model.update(health="not_checked", detail="已配置不代表连接成功")
    if settings.AI_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient(timeout=3, follow_redirects=False) as client:
                response = await client.get(settings.OLLAMA_URL.rstrip("/") + "/api/tags")
                response.raise_for_status()
                names = [m["name"] for m in response.json().get("models", [])]
            ready = settings.OLLAMA_MODEL in names
            model.update(health="ready" if ready else "model_missing", detail="本地服务在线，模型已下载" if ready else "服务在线，请先下载配置的模型")
        except (httpx.HTTPError, ValueError, KeyError):
            model.update(health="offline", detail="本地 Ollama 未响应，请启动模型服务")
    rows = db.query(ResearchRun).order_by(ResearchRun.created_at.desc()).limit(100).all()
    successful = [r for r in rows if r.status == "completed"]
    return {"data_mode": settings.DATA_MODE, "model": model, "single_user": True,
        "catalog_count": db.query(Item).count(), "snapshot_count": db.query(PriceSnapshot).count(),
        "runs": {"sample_size": len(rows), "completed": len(successful), "failed": sum(r.status == "failed" for r in rows),
                 "validated_reports": sum(bool(r.artifact and r.artifact.get("validation", {}).get("validated")) for r in successful if r.artifact and r.artifact.get("validation"))},
        "recent_runs": [{"id": r.id, "session_id": r.session_id, "question": r.question, "status": r.status, "mode": r.answer_mode,
                         "created_at": r.created_at.isoformat()+"Z", "steps": len(r.steps), "sources": len(r.sources)} for r in rows[:10]],
        "checked_at": datetime.utcnow().isoformat()+"Z"}


@router.post("/evaluation")
@limiter.limit("2/minute")
async def run_evaluation(request: Request):
    cases = json.loads((BACKEND / "evaluation/queries.json").read_text())["queries"]
    retriever = get_retriever()
    report = await asyncio.to_thread(evaluate, retriever, cases, 3)
    report.update(executed_at=datetime.utcnow().isoformat()+"Z", top_k=3,
                  note="小规模人工标注检索集；衡量检索排序，不衡量模型事实正确率。")
    return report
