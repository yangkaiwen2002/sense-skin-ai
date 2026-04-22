"""
Decision Engine
===============

Synthesises scoring signals, event signals, and risk factors into a single,
explainable trading recommendation.

Output: BUY | WATCH | HOLD | AVOID

Decision matrix
---------------

The engine accumulates bullish (+) and bearish (-) evidence points, then
maps the net tally to a recommendation bucket with a calibrated confidence.

Signal sources and their maximum point contributions:
  Valuation (low vs 30d avg)     +2 / -2
  Trend (7d momentum)            +1.5 / -1.5
  Event impact (pipeline signal) +2 / -2
  Liquidity (tradability)        +1 / -1
  Overall score tier             +2 / -2
  Risk labels                     -0.5 each (up to -1.5)

Thresholds:
  net >= +3.0  AND total >= 62  →  BUY
  net >= +1.0  AND total >= 52  →  WATCH
  net >= -1.0  AND total >= 42  →  HOLD
  else                          →  AVOID

This is deterministic and traceable — every recommendation can be reproduced
by examining the evidence point log.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.models.item import Item
from app.services.scoring import SkinScore, SubScores
from app.services.event_mapper import EventMapping, EventSignal


# ─── Output type ──────────────────────────────────────────────────────────────

@dataclass
class DecisionResult:
    recommendation:    str       # "BUY" | "WATCH" | "HOLD" | "AVOID"
    recommendation_cn: str       # "买入" | "观望" | "持有" | "规避"
    confidence:        float     # 0.0–1.0
    rationale:         str       # one-sentence primary reason
    upside_factors:    list[str] = field(default_factory=list)
    risk_factors:      list[str] = field(default_factory=list)
    supporting_signals: list[dict] = field(default_factory=list)  # evidence log
    event_context:     list[dict] = field(default_factory=list)
    evidence_sources:  list[str] = field(default_factory=list)
    score_summary:     dict      = field(default_factory=dict)


_REC_CN = {"BUY": "买入", "WATCH": "观望", "HOLD": "持有", "AVOID": "规避"}
_REC_COLORS = {
    "BUY":   "#22c55e",
    "WATCH": "#4a8ef5",
    "HOLD":  "#f5a623",
    "AVOID": "#ef4444",
}


# ─── Main entry point ─────────────────────────────────────────────────────────

def decide(
    item: Item,
    score: SkinScore,
    event_map: EventMapping,
) -> DecisionResult:
    """
    Combine scoring result and event mapping into a final recommendation.
    Every decision is fully traceable through the `supporting_signals` list.
    """
    ss      = score.subscores
    total   = score.total
    val     = score.valuation_label
    impact  = event_map.event_impact_score
    liq     = ss.liquidity
    trend   = ss.trend
    risk_lbl = score.risks  # already populated by scoring.py

    evidence_log: list[dict] = []   # audit trail
    bullish = 0.0
    bearish = 0.0

    # ── 1. Valuation signal ────────────────────────────────────────────────────
    if val == "低估":
        pts = 2.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "估值偏低", f"当前价格低于 30 日均价，估值评分 {ss.valuation}/100"))
    elif val == "高估":
        pts = 2.0
        bearish += pts
        evidence_log.append(_sig("-", pts, "估值偏高", f"当前价格高于 30 日均价，回调风险存在，估值评分 {ss.valuation}/100"))
    else:
        evidence_log.append(_sig("=", 0, "估值合理", f"价格处于历史均值附近，估值评分 {ss.valuation}/100"))

    # ── 2. Trend signal ────────────────────────────────────────────────────────
    if trend >= 68:
        pts = 1.5
        bullish += pts
        evidence_log.append(_sig("+", pts, "趋势强势", f"7 日趋势评分 {trend}/100，价格动能偏多"))
    elif trend >= 55:
        pts = 0.5
        bullish += pts
        evidence_log.append(_sig("+", pts, "趋势温和", f"7 日趋势评分 {trend}/100，小幅偏多"))
    elif trend <= 33:
        pts = 1.5
        bearish += pts
        evidence_log.append(_sig("-", pts, "趋势偏弱", f"7 日趋势评分 {trend}/100，价格动能不足"))
    else:
        evidence_log.append(_sig("=", 0, "趋势中性", f"7 日趋势评分 {trend}/100，方向不明"))

    # ── 3. Event signal ────────────────────────────────────────────────────────
    if impact >= 0.45:
        pts = 2.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "事件强催化", _event_signal_note(event_map, positive=True)))
    elif impact >= 0.20:
        pts = 1.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "事件正面支撑", _event_signal_note(event_map, positive=True)))
    elif impact <= -0.35:
        pts = 2.0
        bearish += pts
        evidence_log.append(_sig("-", pts, "事件负面压制", _event_signal_note(event_map, positive=False)))
    elif impact <= -0.15:
        pts = 1.0
        bearish += pts
        evidence_log.append(_sig("-", pts, "事件轻微压制", _event_signal_note(event_map, positive=False)))
    else:
        evidence_log.append(_sig("=", 0, "事件中性", event_map.event_summary or "当前无明显事件催化"))

    # ── 4. Liquidity signal ────────────────────────────────────────────────────
    if liq >= 65:
        pts = 1.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "流动性充足", f"流动性评分 {liq}/100，市场深度良好，可随时变现"))
    elif liq <= 30:
        pts = 1.0
        bearish += pts
        evidence_log.append(_sig("-", pts, "流动性不足", f"流动性评分 {liq}/100，变现能力受限"))
    else:
        evidence_log.append(_sig("=", 0, "流动性一般", f"流动性评分 {liq}/100"))

    # ── 5. Total score tier ────────────────────────────────────────────────────
    if total >= 74:
        pts = 2.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "综合评分优秀", f"AI 综合评分 {total}/100（阈值: 74+）"))
    elif total >= 62:
        pts = 1.0
        bullish += pts
        evidence_log.append(_sig("+", pts, "综合评分良好", f"AI 综合评分 {total}/100"))
    elif total <= 40:
        pts = 2.0
        bearish += pts
        evidence_log.append(_sig("-", pts, "综合评分较低", f"AI 综合评分 {total}/100，多维度数据偏弱"))
    else:
        evidence_log.append(_sig("=", 0, "综合评分中等", f"AI 综合评分 {total}/100"))

    # ── 6. Risk label penalties ────────────────────────────────────────────────
    for risk in risk_lbl[:3]:
        pts = 0.5
        bearish += pts
        evidence_log.append(_sig("-", pts, "风险因素", risk))

    # ── Decision threshold mapping ─────────────────────────────────────────────
    net = bullish - bearish

    if net >= 3.0 and total >= 62:
        rec = "BUY"
        raw_conf = 0.55 + net * 0.06 + total * 0.002
    elif net >= 1.0 and total >= 52:
        rec = "WATCH"
        raw_conf = 0.50 + net * 0.05 + total * 0.001
    elif net >= -1.0 and total >= 42:
        rec = "HOLD"
        raw_conf = 0.45 + (net + 1.0) * 0.04
    else:
        rec = "AVOID"
        raw_conf = 0.40 + abs(net) * 0.04

    confidence = round(min(0.93, raw_conf), 2)

    # ── Build human-readable outputs ───────────────────────────────────────────
    upsides = _collect_upsides(score, event_map, item)
    risks   = _collect_risks(score, event_map)
    rationale = _build_rationale(rec, item, score, event_map, net)

    # ── Event context for UI ───────────────────────────────────────────────────
    event_context = [
        {
            "title":          e.title,
            "event_type":     e.event_type,
            "window_label":   e.window_label,
            "days_delta":     e.days_delta,
            "impact":         e.impact_direction,
            "strength":       round(e.impact_strength, 2),
            "relevance":      round(e.relevance, 2),
            "source":         e.source,
        }
        for e in event_map.relevant_events[:5]
    ]

    # ── Evidence sources ───────────────────────────────────────────────────────
    sources = _collect_sources(event_map)

    return DecisionResult(
        recommendation     = rec,
        recommendation_cn  = _REC_CN[rec],
        confidence         = confidence,
        rationale          = rationale,
        upside_factors     = upsides[:5],
        risk_factors       = risks[:3],
        supporting_signals = evidence_log,
        event_context      = event_context,
        evidence_sources   = sources,
        score_summary      = {
            "total":     total,
            "rarity":    ss.rarity,
            "exterior":  ss.exterior,
            "liquidity": ss.liquidity,
            "trend":     ss.trend,
            "valuation": ss.valuation,
            "demand":    ss.demand,
            "event":     getattr(ss, "event_signal", event_map.event_signal_score),
            "valuation_label": val,
            "net_signal":      round(net, 2),
        },
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _sig(direction: str, pts: float, label: str, note: str) -> dict:
    return {
        "direction": direction,   # "+" | "-" | "="
        "points":    pts,
        "label":     label,
        "note":      note,
    }


def _event_signal_note(em: EventMapping, positive: bool) -> str:
    if em.relevant_events:
        top = em.relevant_events[0]
        timing = f"（{top.window_label}）"
        return f"{top.title}{timing}，{em.event_summary}"
    return em.event_summary or ("检测到正面市场事件信号" if positive else "检测到负面市场事件信号")


def _collect_upsides(score: SkinScore, em: EventMapping, item: Item) -> list[str]:
    upsides = list(score.reasons_to_buy)

    # Inject top event signal if positive
    if em.event_impact_score > 0.2 and em.relevant_events:
        top = em.relevant_events[0]
        if top.days_delta > 0:
            upsides.insert(0, f"{top.title}（{top.days_delta} 天后开赛），{item.weapon_type or ''}类饰品需求预期上升")
        elif top.days_delta >= -14:
            upsides.insert(0, f"近期{top.event_type}信号正面，市场情绪偏多")

    return upsides


def _collect_risks(score: SkinScore, em: EventMapping) -> list[str]:
    risks = list(score.risks)
    if em.event_impact_score < -0.2 and em.relevant_events:
        neg_events = [e for e in em.relevant_events if e.impact_direction == "negative"]
        if neg_events:
            risks.insert(0, f"市场信号偏空：{neg_events[0].title}产生下行压力")
    return risks


def _build_rationale(
    rec: str,
    item: Item,
    score: SkinScore,
    em: EventMapping,
    net: float,
) -> str:
    val   = score.valuation_label
    total = score.total

    top_event = em.relevant_events[0] if em.relevant_events else None

    if rec == "BUY":
        if top_event and top_event.days_delta > 0 and em.event_impact_score > 0.4:
            return (
                f"{top_event.title}将于 {top_event.days_delta} 天后开始，"
                f"结合{val}估值（评分 {total}）形成明确买入信号"
            )
        elif val == "低估":
            return f"价格低于历史均值且综合评分达 {total}，多维信号共同支持买入"
        else:
            return f"综合评分 {total}、流动性充足，多维度信号倾向买入"

    elif rec == "WATCH":
        if top_event and top_event.days_delta > 0:
            return (
                f"即将到来的{top_event.title}可能提供催化，"
                f"建议持续观望等待更明确方向（评分 {total}）"
            )
        elif val == "合理":
            return f"估值合理、评分 {total}，无强催化信号，建议观望等待机会"
        else:
            return f"信号混合，综合评分 {total}，建议观望"

    elif rec == "HOLD":
        return f"基本面稳定（评分 {total}），无明显做多或做空催化，适合持有等待信号"

    else:  # AVOID
        if val == "高估":
            return f"价格高于历史均值且缺乏事件支撑，综合评分 {total}，规避风险"
        return f"多维度信号偏弱（评分 {total}），当前风险/回报比不理想"


def _collect_sources(em: EventMapping) -> list[str]:
    srcs = {"BUFF163 价格数据库（35 天历史）", "AI 综合评分模型（7 维度）"}
    for e in em.relevant_events[:4]:
        if e.source and e.source not in ("community", "market_pattern"):
            srcs.add(e.source)
        elif e.source == "market_pattern":
            srcs.add("历史价格模式分析")
    return sorted(srcs)


# ─── Serialiser ───────────────────────────────────────────────────────────────

def decision_to_dict(d: DecisionResult) -> dict:
    return {
        "recommendation":    d.recommendation,
        "recommendation_cn": d.recommendation_cn,
        "confidence":        d.confidence,
        "rationale":         d.rationale,
        "upside_factors":    d.upside_factors,
        "risk_factors":      d.risk_factors,
        "supporting_signals": d.supporting_signals,
        "event_context":     d.event_context,
        "evidence_sources":  d.evidence_sources,
        "score_summary":     d.score_summary,
        "color":             _REC_COLORS[d.recommendation],
    }
