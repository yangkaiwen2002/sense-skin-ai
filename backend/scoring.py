"""
Skin Scoring System — rule-based placeholder.
后续可接机器学习模型或更复杂算法，接口不变。
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class SkinScore:
    overall:    int           # 0-100
    value:      int
    liquidity:  int
    stability:  int
    trend:      int

    overall_label:    str     # e.g. "优质标的"
    overall_color:    str     # hex

    value_note:     str
    liquidity_note: str
    stability_note: str
    trend_note:     str

    # raw inputs echoed back for the AI agent
    lowest_price:  float | None
    median_price:  float | None
    volume:        int   | None
    total_listings:int   | None
    price_std:     float | None


def _score_color(s: int) -> str:
    if s >= 75: return "#5cb85c"
    if s >= 55: return "#f0ad4e"
    return "#d9534f"


def compute(
    lowest_price:   float | None = None,
    median_price:   float | None = None,
    volume:         int   | None = None,
    total_listings: int   | None = None,
    listing_prices: list[float] | None = None,
) -> SkinScore:
    """
    All inputs are optional — gracefully degrades when data is sparse.
    """

    # ── VALUE ───────────────────────────────────────────────────────────────
    if lowest_price and median_price and median_price > 0:
        ratio = lowest_price / median_price
        if ratio < 0.93:
            value, value_note = 88, "当前最低价明显低于均价，入手性价比高"
        elif ratio < 0.98:
            value, value_note = 72, "价格接近均价，处于合理区间"
        elif ratio < 1.04:
            value, value_note = 55, "价格略高于均价，可等待回调"
        else:
            value, value_note = 32, "价格显著偏高，建议观望"
    else:
        value, value_note = 50, "价格数据不足，暂无评估"

    # ── LIQUIDITY ───────────────────────────────────────────────────────────
    if volume is None:
        liquidity, liquidity_note = 50, "成交量数据暂缺"
    elif volume > 500:
        liquidity, liquidity_note = 92, "日成交量极高，流动性极佳，随时可变现"
    elif volume > 200:
        liquidity, liquidity_note = 78, "成交活跃，出售通常在数小时内成交"
    elif volume > 50:
        liquidity, liquidity_note = 58, "流动性一般，可能需要 1-3 天出售"
    elif volume > 10:
        liquidity, liquidity_note = 36, "成交量偏低，出售周期较长"
    else:
        liquidity, liquidity_note = 18, "极低成交量，变现困难，风险较高"

    # ── STABILITY ───────────────────────────────────────────────────────────
    prices = listing_prices or []
    if len(prices) >= 5:
        arr = np.array(prices, dtype=float)
        cv  = float(arr.std() / arr.mean()) if arr.mean() > 0 else 0
        if cv < 0.02:
            stability, stability_note = 92, "价格极稳定，波动率极低，适合长期持有"
        elif cv < 0.05:
            stability, stability_note = 76, "价格较稳定，短期内大幅波动可能性低"
        elif cv < 0.10:
            stability, stability_note = 56, "价格存在一定波动，建议关注近期走势"
        elif cv < 0.18:
            stability, stability_note = 36, "价格波动较大，持仓风险偏高"
        else:
            stability, stability_note = 20, "价格剧烈波动，高风险，慎重入手"
    elif len(prices) > 0:
        stability, stability_note = 50, "挂单样本较少，稳定性评估待补充"
    else:
        stability, stability_note = 50, "暂无挂单数据"

    # ── TREND ───────────────────────────────────────────────────────────────
    # Proxy: supply/demand ratio (listings ÷ daily volume)
    if total_listings and volume and volume > 0:
        ratio = total_listings / volume
        if ratio < 1.5:
            trend, trend_note = 82, "供不应求，价格有上涨动力"
        elif ratio < 4:
            trend, trend_note = 65, "供需基本平衡，价格短期较稳"
        elif ratio < 10:
            trend, trend_note = 46, "供大于求，价格存在下行压力"
        else:
            trend, trend_note = 28, "严重供过于求，价格下行风险高"
    else:
        trend, trend_note = 50, "接入历史价格数据后趋势评分将更精准"

    # ── OVERALL ─────────────────────────────────────────────────────────────
    overall = int(
        value     * 0.30 +
        liquidity * 0.25 +
        stability * 0.25 +
        trend     * 0.20
    )

    if overall >= 75: overall_label = "优质标的"
    elif overall >= 62: overall_label = "值得关注"
    elif overall >= 48: overall_label = "谨慎持有"
    else:              overall_label = "建议观望"

    price_std = float(np.std(prices)) if len(prices) >= 2 else None

    return SkinScore(
        overall=overall, value=value, liquidity=liquidity,
        stability=stability, trend=trend,
        overall_label=overall_label, overall_color=_score_color(overall),
        value_note=value_note, liquidity_note=liquidity_note,
        stability_note=stability_note, trend_note=trend_note,
        lowest_price=lowest_price, median_price=median_price,
        volume=volume, total_listings=total_listings, price_std=price_std,
    )


# ── Rule-based AI agent responses ───────────────────────────────────────────

def agent_reply(question: str, hash_name: str, sc: SkinScore) -> str:
    """
    Contextual rule-based reply. Replace with LLM call later.
    """
    q = question.strip().lower()
    name = hash_name.split("|")[-1].strip() if "|" in hash_name else hash_name
    lp = f"¥{sc.lowest_price:.2f}" if sc.lowest_price else "N/A"
    mp = f"¥{sc.median_price:.2f}" if sc.median_price else "N/A"

    # ── 买入类 ──────────────────────────────────────────────────────────────
    if any(w in q for w in ["买", "入手", "购入", "值不值", "该买"]):
        if sc.overall >= 72:
            return (
                f"**{name}** 综合评分 {sc.overall}/100，属于「{sc.overall_label}」。\n\n"
                f"当前最低卖价 {lp}，{sc.value_note}，入手时机尚可。\n"
                f"流动性{sc.liquidity_note}，若需要出手不会太难。\n\n"
                f"💡 建议：整体评分较高，若预算充足可以考虑入手，"
                f"但仍建议对比 BUFF / 悠悠有品价格后下单。"
            )
        elif sc.overall >= 50:
            return (
                f"**{name}** 综合评分 {sc.overall}/100，属于「{sc.overall_label}」。\n\n"
                f"{sc.value_note}。{sc.trend_note}。\n\n"
                f"💡 建议：目前不是最优入手时机，建议等待价格回落至均价（{mp}）"
                f"附近再考虑购入。"
            )
        else:
            return (
                f"**{name}** 综合评分仅 {sc.overall}/100，评级「{sc.overall_label}」。\n\n"
                f"问题集中在：{sc.value_note}；{sc.stability_note}。\n\n"
                f"❌ 不建议当前入手。等待市场信号改善后再评估。"
            )

    # ── 持有类 ──────────────────────────────────────────────────────────────
    elif any(w in q for w in ["持有", "拿着", "长期", "hold", "保值"]):
        if sc.stability >= 70:
            return (
                f"**{name}** 稳定性评分 {sc.stability}/100 —— {sc.stability_note}\n\n"
                f"趋势方面：{sc.trend_note}\n\n"
                f"💡 稳定性较高，适合中长期持有。建议设置目标价位，"
                f"当价格超过当前均价（{mp}）15% 以上时考虑出手。"
            )
        else:
            return (
                f"**{name}** 稳定性评分 {sc.stability}/100 —— {sc.stability_note}\n\n"
                f"趋势方面：{sc.trend_note}\n\n"
                f"⚠️ 当前稳定性一般，长期持有风险偏高。"
                f"若非情怀向，建议控制仓位，不宜重仓持有。"
            )

    # ── 卖出类 ──────────────────────────────────────────────────────────────
    elif any(w in q for w in ["卖", "出手", "出售", "抛"]):
        if sc.liquidity >= 70:
            return (
                f"**{name}** 流动性评分 {sc.liquidity}/100 —— {sc.liquidity_note}\n\n"
                f"当前最低在售价 {lp}，均价 {mp}。\n\n"
                f"💡 流动性良好，出售不难。建议挂单价格参考均价附近，"
                f"若急于变现可略低 3-5% 快速成交。"
            )
        else:
            return (
                f"**{name}** 流动性评分 {sc.liquidity}/100 —— {sc.liquidity_note}\n\n"
                f"⚠️ 流动性偏低，出售可能需要等待较长时间。"
                f"建议参考 {lp} 左右挂单，并保持耐心。"
                f"若急需资金，可能需要接受低于均价 10% 以上的成交价。"
            )

    # ── 解释分数 ─────────────────────────────────────────────────────────────
    elif any(w in q for w in ["分数", "为什么", "评分", "低", "高", "解释"]):
        weak = []
        if sc.value     < 55: weak.append(f"价值分偏低（{sc.value}）：{sc.value_note}")
        if sc.liquidity < 55: weak.append(f"流动性偏低（{sc.liquidity}）：{sc.liquidity_note}")
        if sc.stability < 55: weak.append(f"稳定性不足（{sc.stability}）：{sc.stability_note}")
        if sc.trend     < 55: weak.append(f"趋势偏弱（{sc.trend}）：{sc.trend_note}")

        if weak:
            issues = "\n".join(f"• {w}" for w in weak)
            return (
                f"**{name}** 综合评分 {sc.overall}/100，拉低评分的主要因素：\n\n"
                f"{issues}\n\n"
                f"改善方向：关注价格回调（目标均价 {mp}），"
                f"以及市场成交量变化。"
            )
        else:
            return (
                f"**{name}** 综合评分 {sc.overall}/100，各维度均衡：\n\n"
                f"• 价值 {sc.value} · 流动性 {sc.liquidity} "
                f"· 稳定性 {sc.stability} · 趋势 {sc.trend}\n\n"
                f"整体表现良好，无明显短板。"
            )

    # ── 通用分析 ─────────────────────────────────────────────────────────────
    else:
        return (
            f"**{name}** 综合分析：\n\n"
            f"• 当前最低价 {lp}，均价 {mp}\n"
            f"• 综合评分 {sc.overall}/100（{sc.overall_label}）\n"
            f"• {sc.value_note}\n"
            f"• {sc.liquidity_note}\n"
            f"• {sc.stability_note}\n\n"
            f"如需深入分析，可以问我：「值得买吗」「适合长期持有吗」"
            f"「为什么分数低」等具体问题。"
        )
