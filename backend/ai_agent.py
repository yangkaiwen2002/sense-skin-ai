"""
Real Claude AI agent for SkinSense.
Uses claude-opus-4-6 with full skin market context.
"""
import os
from typing import Generator
import anthropic
from dotenv import load_dotenv

load_dotenv()

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("未找到 API key，请在 .env 中设置 CLAUDE_API_KEY")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _build_system(hash_name: str, sc, listings: dict, overview: dict) -> str:
    """Build a rich system prompt with all current market context."""

    # Price data
    lp  = sc.lowest_price
    mp  = sc.median_price
    vol = sc.volume
    tot = sc.total_listings
    std = sc.price_std

    price_lines = []
    if lp:  price_lines.append(f"- 最低在售价: ¥{lp:.2f}")
    if mp:  price_lines.append(f"- 市场中位价: ¥{mp:.2f}")
    if lp and mp and mp > 0:
        delta = (lp - mp) / mp * 100
        price_lines.append(f"- 最低价 vs 均价: {delta:+.1f}%")
    if vol:  price_lines.append(f"- 日成交量: {vol:,} 件")
    if tot:  price_lines.append(f"- 当前挂单总量: {tot:,} 件")
    if std:  price_lines.append(f"- 价格标准差: ¥{std:.2f}")
    if tot and vol and vol > 0:
        price_lines.append(f"- 供需比（挂单/日成交）: {tot/vol:.1f}x")

    # Sample listing prices
    raw_listings = listings.get("listings", [])
    sample_prices = [l["price"] for l in raw_listings[:15]]
    prices_str = "  ".join(f"¥{p:.2f}" for p in sample_prices) if sample_prices else "暂无"

    price_section = "\n".join(price_lines) if price_lines else "暂无市场数据"

    return f"""你是 SkinSense AI，一个专业的 CS2（反恐精英2）饰品市场分析助手。你对 CS2 饰品市场有深入了解，包括：Steam 社区市场、BUFF 市场、悠悠有品、网易 BUFF 等平台；皮肤的稀有度、磨损度、花纹、印花；市场价格走势；饰品投资策略；常见武器和皮肤系列。

━━━ 当前分析饰品 ━━━
{hash_name}

━━━ 实时市场数据 ━━━
{price_section}

当前最低挂单价格样本（从低到高）:
{prices_str}

━━━ AI 综合评分 ━━━
综合评分: {sc.overall}/100 — {sc.overall_label}
  • 价值分   {sc.value}/100: {sc.value_note}
  • 流动性   {sc.liquidity}/100: {sc.liquidity_note}
  • 稳定性   {sc.stability}/100: {sc.stability_note}
  • 趋势分   {sc.trend}/100: {sc.trend_note}

━━━ 你的职责 ━━━
基于以上数据 + 你对 CS2 市场的知识，回答用户关于这个饰品的任何问题，例如：
- 现在值不值得买/卖/持有
- 同价位有没有更值得入手的饰品（给出具体名称和理由）
- 价格未来走势预测
- 这个皮肤的背景、稀有度、受欢迎程度
- 与 BUFF/悠悠有品价格差异通常多少
- 磨损对价值的影响
- 任何 CS2 饰品相关问题

回答要有实质内容，给出具体建议而非模糊回答。用中文回答，除非用户用英文。不要重复已知数据，重点给出额外洞察和建议。回答简洁有力，避免废话。"""


def ask_agent_stream(
    question: str,
    hash_name: str,
    sc,
    listings: dict,
    overview: dict,
    history: list[dict],
) -> Generator[str, None, None]:
    """
    Stream Claude's response token by token.
    history: list of {"role": "user"|"assistant", "content": str}
    """
    client = _get_client()
    system = _build_system(hash_name, sc, listings, overview)

    # Build messages: history + new question
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
    ]
    messages.append({"role": "user", "content": question})

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield text
