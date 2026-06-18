"""
RAG (Retrieval-Augmented Generation) endpoint for SkinSense.

Flow:
  1. Receive user question
  2. Retrieve top-k relevant knowledge entries (TF-IDF, local)
  3. Build prompt: question + retrieved context
  4. Stream answer via Claude claude-opus-4-6 (same pattern as chat.py)
  5. SSE events: sources JSON first, then text chunks, then [DONE]
"""

import json
import anthropic
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.limiter import limiter
from app.rag.retriever import get_retriever

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGRequest(BaseModel):
    question: str
    top_k: int = 3


_SYSTEM = """你是 SkinSense AI，一个专业的 CS2（反恐精英2）饰品市场分析助手。

你的回答必须以下面提供的【知识库参考内容】为主要依据，在此基础上结合你对 CS2 市场的知识进行补充分析。不要编造具体价格数字，若知识库未覆盖某问题，请如实说明并提供一般性分析。

回答要求：
- 有实质内容，给出具体建议和分析
- 简洁有力，避免废话
- 用中文回答，除非用户用英文提问
- 可以引用知识库中的具体数据支撑你的观点"""


def _build_prompt(question: str, context: str) -> str:
    return f"""【知识库参考内容】
{context}

━━━━━━━━━━━━━━━━

【用户问题】
{question}

请基于以上知识库内容和你的 CS2 市场知识，给出专业、具体的回答。"""


@router.post("/query")
@limiter.limit("20/5minute")
def rag_query(request: Request, req: RAGRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    api_key = settings.CLAUDE_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Claude API key not configured")

    retriever = get_retriever()
    retrieved = retriever.query(req.question, top_k=req.top_k)
    context = retriever.format_context(retrieved)

    sources = [{"id": e["id"], "title": e["title"], "category": e["category"]} for e in retrieved]
    prompt = _build_prompt(req.question, context)

    def generate():
        # First event: emit sources so the frontend can display them immediately
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        try:
            client = anthropic.Anthropic(api_key=api_key)
            with client.messages.stream(
                model="claude-opus-4-6",
                max_tokens=1024,
                system=_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
