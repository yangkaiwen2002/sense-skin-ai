"""
RAG (Retrieval-Augmented Generation) endpoint for SkinSense.

Flow:
  1. Receive user question
  2. Retrieve top-k relevant knowledge entries via hybrid search:
     FAISS (semantic) + BM25 (keyword) + char-level TF-IDF (exact CN/EN
     substrings), fused with weighted Reciprocal Rank Fusion — see
     app/rag/retriever.py, app/rag/fusion.py
  3. Build prompt: question + retrieved context
  4. Stream answer via Claude claude-opus-4-6 (same pattern as chat.py)
  5. SSE events: sources JSON first (now also carrying which retrievers
     were active and the fused score), then text chunks, then [DONE]
"""

import json
import logging

import anthropic
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.limiter import limiter
from app.rag.retriever import MAX_TOP_K, get_retriever
from app.rag.models import KnowledgeBaseError

router = APIRouter(prefix="/rag", tags=["rag"])
logger = logging.getLogger(__name__)


class RAGRequest(BaseModel):
    question: str = Field(max_length=2000)
    top_k: int = Field(default=3, ge=1, le=MAX_TOP_K)


_SYSTEM = """你是 SkinSense AI，一个专业的 CS2（反恐精英2）饰品市场分析助手。

下面的【知识库参考内容】来自一个混合检索系统（语义向量检索 + 关键词检索 + 字符级精确匹配融合排序），你的回答必须以此为主要依据，在此基础上结合你对 CS2 市场的知识进行补充分析。不要编造具体价格数字。若【知识库参考内容】为空或明确标注"未找到相关知识库内容"，你必须如实告知用户知识库未覆盖该问题，只能给出一般性分析，不能暗示或假装这些内容来自知识库。

回答要求：
- 有实质内容，给出具体建议和分析
- 简洁有力，避免废话
- 用中文回答，除非用户用英文提问
- 可以引用知识库中的具体数据支撑你的观点
- 不要向用户复述检索分数、排名等内部实现细节，那些不是分析内容"""

_SYSTEM += "\n- 引用参考内容时标注 [知识 1] 等对应编号。知识库是静态参考资料，价格、费率和历史收益描述不代表当前行情或经核验的事实；不要把它们表述为最新报价。"


def _search(req: RAGRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    try:
        return get_retriever().search(req.question, top_k=req.top_k)
    except KnowledgeBaseError:
        logger.exception("Knowledge base unavailable")
        raise HTTPException(status_code=503, detail="知识库暂不可用，请稍后重试") from None


@router.post("/search")
@limiter.limit("60/minute")
def rag_search(request: Request, req: RAGRequest):
    """Inspect knowledge and retrieval evidence without an LLM API key."""
    return _search(req)


def _build_prompt(question: str, context: str, has_context: bool) -> str:
    note = (
        ""
        if has_context
        else "\n（注意：本次未检索到相关知识库内容，请明确告知用户这一点，仅基于你的通用知识谨慎作答，不要暗示信息来自知识库。）"
    )
    return f"""【知识库参考内容】
{context}
{note}
━━━━━━━━━━━━━━━━

【用户问题】
{question}

请基于以上知识库内容和你的 CS2 市场知识，给出专业、具体的回答。"""


@router.post("/query")
@limiter.limit("20/5minute")
def rag_query(request: Request, req: RAGRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    search = _search(req)
    retrieved = search["results"]
    retriever = get_retriever()
    context = retriever.format_context(retrieved)
    active_retrievers = search["meta"]["active_retrievers"]
    api_key = settings.CLAUDE_API_KEY

    logger.info(
        "rag_query active_retrievers=%s results=%d faiss_disabled_reason=%s",
        active_retrievers, len(retrieved), retriever.faiss_disabled_reason,
    )

    # Backward-compatible fields (id/title/category) plus additive hybrid-search
    # metadata (fused_score, active_retrievers) — old frontend code that only
    # reads id/title/category keeps working unchanged.
    sources = [
        {
            "id": e["id"],
            "title": e["title"],
            "category": e["category"],
            "content": e["content"],
            "fused_score": e.get("fused_score", e.get("score")),
            "retrieval_details": e.get("retrieval_details"),
        }
        for e in retrieved
    ]
    prompt = _build_prompt(req.question, context, has_context=bool(retrieved))

    def generate():
        # First event: emit sources (+ which retrievers were active) so the
        # frontend can display them immediately.
        meta = {**search["meta"], "answer_mode": "generated" if api_key else "retrieval_only"}
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'meta': meta})}\n\n"

        if not api_key:
            yield f"data: {json.dumps({'type': 'notice', 'text': '当前为知识检索模式，可展开阅读原文；配置 Claude API 后可生成综合回答。'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        try:
            with anthropic.Anthropic(api_key=api_key, timeout=45.0, max_retries=1) as client, client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
        except Exception:
            logger.exception("RAG generation failed")
            yield f"data: {json.dumps({'type': 'error', 'error': 'AI 回答暂时不可用，已保留检索来源，请稍后重试。'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
