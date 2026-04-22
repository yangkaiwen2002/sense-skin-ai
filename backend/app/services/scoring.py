"""
Skin Scoring Engine — 7-dimensional scoring with event awareness.

Dimensions and weights:
  rarity       18%  scarcity and collector demand
  exterior     12%  condition / float quality
  liquidity    18%  tradability, market depth
  trend        14%  price momentum (7d)
  valuation    14%  current price vs 30d average
  demand       12%  weapon category × rarity × stattrak
  event_signal 12%  external market signal from event pipeline

The event_signal dimension is fed from event_mapper.EventMapping.
When no mapping is provided, it defaults to 50 (neutral).
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.utils.metrics import (
    compute_avg, compute_return, compute_volatility, compute_liquidity_score,
)

if TYPE_CHECKING:
    from app.services.event_mapper import EventMapping


# ─── Lookup tables ────────────────────────────────────────────────────────────

RARITY_SCORES: dict[str, int] = {
    "违禁": 95, "隐秘": 85, "保密": 70,
    "受限": 55, "军规": 40, "精工": 32, "普通": 20,
}
EXTERIOR_SCORES: dict[str, int] = {
    "崭新出厂": 95, "略有磨损": 80, "久经沙场": 60,
    "破损不堪": 38, "战痕累累": 22,
}
CATEGORY_DEMAND_BASE: dict[str, int] = {
    "刀": 80, "手套": 75, "狙击枪": 65, "步枪": 60,
    "手枪": 55, "冲锋枪": 45, "霰弹枪": 35, "机枪": 28,
}

WEIGHTS = {
    "rarity":       0.18,
    "exterior":     0.12,
    "liquidity":    0.18,
    "trend":        0.14,
    "valuation":    0.14,
    "demand":       0.12,
    "event_signal": 0.12,
}


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class SubScores:
    rarity:       int
    exterior:     int
    liquidity:    int
    trend:        int
    valuation:    int
    demand:       int
    event_signal: int = 50   # neutral default when no event pipeline data


@dataclass
class SkinScore:
    total:           int
    subscores:       SubScores
    valuation_label: str         # "低估" | "合理" | "高估"
    confidence:      float
    reasons_to_buy:  list[str] = field(default_factory=list)
    risks:           list[str]  = field(default_factory=list)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float = 0, hi: float = 100) -> int:
    return int(max(lo, min(hi, round(v))))


def _build_reasons_and_risks(
    item: Item,
    ss: SubScores,
    ret7d: float,
    cur: float,
    avg30: float,
    volatility: Optional[float],
    event_map: Optional["EventMapping"] = None,
) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    risks:   list[str] = []

    # Rarity
    if ss.rarity >= 95:
        reasons.append("违禁级品（全球仅 M4A4 | Howl），收藏价值极为稀缺")
    elif ss.rarity >= 85:
        reasons.append("隐秘级稀有度，市场流通量极少，长期保值性强")
    elif ss.rarity >= 70:
        reasons.append(f"保密级稀有度（{item.rarity}），具备一定收藏溢价")

    # Exterior
    if ss.exterior >= 90:
        reasons.append("崭新出厂品相，磨损最低，适合收藏及溢价流转")
    elif ss.exterior >= 75:
        reasons.append("略有磨损品相良好，外观接近全新，持有价值稳定")

    # Liquidity
    if ss.liquidity >= 65:
        reasons.append(f"市场流动性良好（{ss.liquidity}/100），随时可变现")
    elif ss.liquidity < 35:
        risks.append(f"流动性偏低（{ss.liquidity}/100），急售时可能承受折价")

    # Trend
    pct = abs(ret7d * 100)
    if ss.trend >= 70:
        reasons.append(f"近 7 日上涨 {pct:.1f}%，短期价格动能较强")
    elif ss.trend >= 58:
        reasons.append(f"近 7 日小幅上涨 {pct:.1f}%，趋势平稳")
    elif ss.trend <= 32:
        risks.append(f"近 7 日下跌 {pct:.1f}%，短期价格动能偏弱")

    # Valuation
    if avg30 > 0:
        delta_pct = (avg30 - cur) / avg30 * 100
        if ss.valuation >= 68:
            reasons.append(f"当前价格低于 30 日均价 {delta_pct:.1f}%，存在回归空间")
        elif ss.valuation <= 35:
            over_pct = abs(delta_pct)
            risks.append(f"当前价格高于 30 日均价 {over_pct:.1f}%，短期有回调压力")

    # Weapon category
    if item.weapon_type in ("刀", "手套"):
        reasons.append("刀/手套类历史保值性极强，高端玩家需求持续稳定")
    elif item.weapon_type == "狙击枪" and ss.rarity >= 70:
        reasons.append("高稀有度狙击枪受职业赛事关注度影响较大，需求较稳")

    # StatTrak
    if item.stattrak:
        reasons.append("StatTrak™ 版本，计数器功能带来独特收藏溢价")

    # Volatility risk
    if volatility and volatility > 0.045:
        risks.append(f"价格波动率偏高（{volatility*100:.1f}%），短期不确定性较大")

    # Event signal
    if event_map is not None:
        if event_map.event_impact_score > 0.4 and event_map.relevant_events:
            top = event_map.relevant_events[0]
            if top.days_delta > 0:
                reasons.append(
                    f"{top.title}（{top.days_delta} 天后）将带来市场催化，"
                    f"历史规律显示此类事件期间需求上升"
                )
            else:
                reasons.append(f"近期市场事件信号正面：{top.title}形成短期支撑")
        elif event_map.event_impact_score < -0.3 and event_map.relevant_events:
            neg = [e for e in event_map.relevant_events if e.impact_direction == "negative"]
            if neg:
                risks.append(f"市场信号偏空：{neg[0].title}产生下行压力（{abs(neg[0].days_delta)} 天前）")

    return reasons[:5], risks[:3]


# ─── Main public function ─────────────────────────────────────────────────────

def score_item(
    db: Session,
    item_id: int,
    event_map: Optional["EventMapping"] = None,
) -> Optional[SkinScore]:
    """
    Compute a full SkinScore for the given item.
    Optionally accepts a pre-computed EventMapping to include event_signal dimension.
    Returns None if item not found or no price data exists.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    buff_plat = db.query(Platform).filter(Platform.name == "BUFF").first()
    if buff_plat:
        snaps = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.item_id == item_id, PriceSnapshot.platform_id == buff_plat.id)
            .order_by(PriceSnapshot.snapshot_time.asc())
            .all()
        )
    else:
        snaps = (
            db.query(PriceSnapshot)
            .filter(PriceSnapshot.item_id == item_id)
            .order_by(PriceSnapshot.snapshot_time.asc())
            .all()
        )

    if not snaps:
        return None

    prices = [s.listing_price for s in snaps if s.listing_price is not None]
    if not prices:
        return None

    latest = snaps[-1]
    cur    = latest.listing_price or 0.0
    avg30  = compute_avg(prices, 30) or cur
    ret7d  = compute_return(prices, 7) or 0.0
    vol    = compute_volatility(prices[-30:])

    volumes = [s.volume_24h for s in snaps[-7:] if s.volume_24h is not None]
    depths  = [s.liquidity_depth for s in snaps[-7:] if s.liquidity_depth is not None]
    raw_liq = compute_liquidity_score(
        sum(volumes) / len(volumes) if volumes else None,
        sum(depths)  / len(depths)  if depths  else None,
        latest.spread, cur,
    )

    # ── Sub-scores ─────────────────────────────────────────────────────────────
    rarity_score    = RARITY_SCORES.get(item.rarity or "", 40)
    exterior_score  = EXTERIOR_SCORES.get(item.exterior or "", 50)
    liquidity_score = _clamp(raw_liq or 40)
    trend_score     = _clamp(50 + ret7d * 800)

    if avg30 > 0:
        delta           = (avg30 - cur) / avg30
        valuation_score = _clamp(50 + delta * 400)
    else:
        valuation_score = 50

    demand_base     = CATEGORY_DEMAND_BASE.get(item.weapon_type or "", 40)
    demand_score    = _clamp(demand_base + (rarity_score - 40) * 0.20 + (10 if item.stattrak else 0))

    # Event signal dimension
    event_signal_score = event_map.event_signal_score if event_map is not None else 50

    # ── Weighted total ──────────────────────────────────────────────────────────
    total = _clamp(
        rarity_score       * WEIGHTS["rarity"]       +
        exterior_score     * WEIGHTS["exterior"]     +
        liquidity_score    * WEIGHTS["liquidity"]    +
        trend_score        * WEIGHTS["trend"]        +
        valuation_score    * WEIGHTS["valuation"]    +
        demand_score       * WEIGHTS["demand"]       +
        event_signal_score * WEIGHTS["event_signal"]
    )

    # ── Valuation label ─────────────────────────────────────────────────────────
    if valuation_score >= 65:
        val_label = "低估"
    elif valuation_score >= 40:
        val_label = "合理"
    else:
        val_label = "高估"

    ss = SubScores(
        rarity       = rarity_score,
        exterior     = exterior_score,
        liquidity    = liquidity_score,
        trend        = trend_score,
        valuation    = valuation_score,
        demand       = demand_score,
        event_signal = event_signal_score,
    )

    reasons, risks = _build_reasons_and_risks(item, ss, ret7d, cur, avg30, vol, event_map)

    # Confidence
    data_coverage = min(len(prices) / 30, 1.0)
    liq_factor    = min(liquidity_score / 100, 1.0)
    event_factor  = 0.05 if event_map and event_map.relevant_events else 0.0
    confidence    = round(0.38 + 0.32 * data_coverage + 0.20 * liq_factor + event_factor, 2)

    return SkinScore(
        total           = total,
        subscores       = ss,
        valuation_label = val_label,
        confidence      = confidence,
        reasons_to_buy  = reasons,
        risks           = risks,
    )


def score_item_dict(
    db: Session,
    item_id: int,
    event_map: Optional["EventMapping"] = None,
) -> Optional[dict]:
    s = score_item(db, item_id, event_map)
    if s is None:
        return None
    return {
        "item_id":         item_id,
        "total_score":     s.total,
        "subscores": {
            "rarity":       s.subscores.rarity,
            "exterior":     s.subscores.exterior,
            "liquidity":    s.subscores.liquidity,
            "trend":        s.subscores.trend,
            "valuation":    s.subscores.valuation,
            "demand":       s.subscores.demand,
            "event_signal": s.subscores.event_signal,
        },
        "valuation_label": s.valuation_label,
        "confidence":      s.confidence,
        "reasons_to_buy":  s.reasons_to_buy,
        "risks":           s.risks,
    }
