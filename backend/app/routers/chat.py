"""AI chat streaming endpoint for SkinSense."""
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.models.item import Item
from app.services.analytics_service import get_item_overview

router = APIRouter(prefix="/items", tags=["chat"])

RARITY_CN = {
    "违禁": "Contraband", "隐秘": "Covert", "保密": "Classified",
    "受限": "Restricted", "军规": "Mil-Spec", "精工": "Industrial Grade",
}


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def _build_system(item: Item, overview) -> str:
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

    return f"""你是 SkinSense AI，一个专业的 CS2（反恐精英2）饰品市场分析助手。你对 CS2 饰品市场有深入了解，包括 Steam、BUFF、悠悠有品、IGXE 等平台，皮肤稀有度、磨损、花纹、印花，市场价格走势，饰品投资策略。

━━━ 当前分析饰品 ━━━
名称: {item.item_name}
武器: {item.weapon_type or "未知"} | 皮肤: {item.skin_name or "未知"}
稀有度: {item.rarity or "未知"} | 磨损: {item.exterior or "未知"}
StatTrak: {"是" if item.stattrak else "否"} | 纪念品: {"是" if item.souvenir else "否"}

━━━ 实时市场数据 ━━━
{price_section}

跨平台价格对比:
{platform_section}

━━━ 你的职责 ━━━
基于以上数据 + 你对 CS2 市场的知识，回答用户关于这个饰品的任何问题：
- 现在值不值得买/卖/持有
- 同价位有没有更值得入手的饰品（给出具体名称和理由）
- 价格未来走势预测
- 皮肤背景、稀有度、受欢迎程度
- 与 BUFF/悠悠有品价格差异
- 磨损对价值的影响
- 任何 CS2 饰品相关问题

回答要有实质内容，给出具体建议。用中文回答，除非用户用英文。不要重复已知数据，重点给出额外洞察和建议。简洁有力，避免废话。"""


@router.post("/{item_id}/chat")
def chat_stream(item_id: int, req: ChatRequest, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    overview = get_item_overview(db, item_id)

    api_key = settings.CLAUDE_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Claude API key not configured")

    system_prompt = _build_system(item, overview)
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
