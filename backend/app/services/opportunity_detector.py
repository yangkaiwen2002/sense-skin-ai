"""
Opportunity Detector — scans all items and surfaces investment opportunities.

An "opportunity" satisfies:
  - total_score >= 58  (decent overall quality)
  - AND one of:
      • valuation_label == "低估"  (price below 30d avg)
      • trend score >= 62          (positive momentum)
      • total_score >= 72          (simply a great skin at fair price)

Results include the full decision engine output (BUY/WATCH/HOLD/AVOID)
and event context, scored with active market events.
"""

from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.services.scoring import score_item
from app.services.event_ingestion import get_active_events
from app.services.event_mapper import map_events_to_item
from app.services.decision_engine import decide

_REC_COLORS = {
    "BUY":   "#22c55e",
    "WATCH": "#4a8ef5",
    "HOLD":  "#f5a623",
    "AVOID": "#ef4444",
}
_REC_CN = {"BUY": "买入", "WATCH": "观望", "HOLD": "持有", "AVOID": "规避"}


# ── tier thresholds ──────────────────────────────────────────────────────────
def _opportunity_tier(total: int, valuation: str, trend: int, rec: str) -> tuple[str, str]:
    """Return (tier_label, tier_color) for display, incorporating decision."""
    if rec == "BUY" and total >= 70:
        return "强力推荐", "#22c55e"
    if rec in ("BUY", "WATCH") and (valuation == "低估" or total >= 65):
        return "值得关注", "#4a8ef5"
    if valuation == "低估":
        return "价值低估", "#f5a623"
    if trend >= 62:
        return "趋势上涨", "#8b5cf6"
    return "综合优质", "#5e98d9"


def _get_current_price(db: Session, item_id: int, buff_id: int | None) -> float | None:
    if buff_id is None:
        return None
    snap = (
        db.query(PriceSnapshot)
        .filter(
            PriceSnapshot.item_id == item_id,
            PriceSnapshot.platform_id == buff_id,
        )
        .order_by(PriceSnapshot.snapshot_time.desc())
        .first()
    )
    return snap.listing_price if snap else None


# ── public entry point ───────────────────────────────────────────────────────
def detect_opportunities(db: Session, limit: int = 8) -> list[dict]:
    """
    Score every item with full event context and return the top `limit` opportunities.
    Each result includes the decision engine recommendation and event summary.
    """
    buff_plat = db.query(Platform).filter(Platform.name == "BUFF").first()
    buff_id   = buff_plat.id if buff_plat else None

    # Load active events once — reused for all items (no repeated I/O)
    active_events = get_active_events(days=90)

    items   = db.query(Item).all()
    results = []

    for item in items:
        # Map events to item (pure Python, no DB call)
        event_map = map_events_to_item(item, active_events)

        # Score with event context
        s = score_item(db, item.id, event_map=event_map)
        if s is None:
            continue

        # Filter: must clear the baseline score threshold
        if s.total < 55:
            continue

        # At least one positive signal beyond baseline quality
        is_opp = (
            s.valuation_label == "低估"
            or s.subscores.trend >= 62
            or s.total >= 70
            or event_map.event_impact_score >= 0.3
        )
        if not is_opp:
            continue

        # Run decision engine for the recommendation signal
        decision = decide(item, s, event_map)
        # Skip AVOID items from the opportunity feed
        if decision.recommendation == "AVOID":
            continue

        price = _get_current_price(db, item.id, buff_id)
        tier_label, tier_color = _opportunity_tier(
            s.total, s.valuation_label, s.subscores.trend, decision.recommendation
        )

        # Top event context for display
        top_event = event_map.relevant_events[0] if event_map.relevant_events else None

        results.append({
            "item_id":           item.id,
            "item_name":         item.item_name,
            "skin_name":         item.skin_name or item.item_name,
            "weapon_type":       item.weapon_type,
            "rarity":            item.rarity,
            "exterior":          item.exterior,
            "stattrak":          item.stattrak,
            "icon_url":          item.icon_url,
            "total_score":       s.total,
            "valuation_label":   s.valuation_label,
            "tier_label":        tier_label,
            "tier_color":        tier_color,
            "current_price":     price,
            "trend_score":       s.subscores.trend,
            "liquidity_score":   s.subscores.liquidity,
            "event_score":       s.subscores.event_signal,
            "top_reason":        s.reasons_to_buy[0] if s.reasons_to_buy else "综合评分优质",
            # Decision engine output
            "recommendation":    decision.recommendation,
            "recommendation_cn": decision.recommendation_cn,
            "rec_color":         _REC_COLORS.get(decision.recommendation, "#f5a623"),
            "confidence":        decision.confidence,
            "rationale":         decision.rationale,
            # Event context
            "event_summary":     event_map.event_summary if event_map.relevant_events else None,
            "event_impact":      round(event_map.event_impact_score, 2),
            "top_event_title":   top_event.title if top_event else None,
            "top_event_window":  top_event.window_label if top_event else None,
        })

    # Sort: BUY first, then by score DESC
    rec_order  = {"BUY": 0, "WATCH": 1, "HOLD": 2, "AVOID": 3}
    tier_order = {"强力推荐": 0, "值得关注": 1, "价值低估": 2, "趋势上涨": 3, "综合优质": 4}
    results.sort(key=lambda x: (
        rec_order.get(x["recommendation"], 9),
        -x["total_score"],
        tier_order.get(x["tier_label"], 9),
    ))

    return results[:limit]


def get_market_summary(db: Session) -> dict:
    """
    Market-level summary stats. Loads events once and scores all items with full context.
    """
    buff_plat = db.query(Platform).filter(Platform.name == "BUFF").first()
    if not buff_plat:
        return {}

    active_events = get_active_events(days=90)
    items = db.query(Item).all()

    scores_list  = []
    trend_ups    = 0
    trend_downs  = 0
    undervalued  = 0
    buy_signals  = 0
    watch_signals = 0

    for item in items:
        event_map = map_events_to_item(item, active_events)
        s = score_item(db, item.id, event_map=event_map)
        if s is None:
            continue
        scores_list.append(s.total)
        if s.subscores.trend >= 55:
            trend_ups += 1
        elif s.subscores.trend < 45:
            trend_downs += 1
        if s.valuation_label == "低估":
            undervalued += 1
        try:
            d = decide(item, s, event_map)
            if d.recommendation == "BUY":
                buy_signals += 1
            elif d.recommendation == "WATCH":
                watch_signals += 1
        except Exception:
            pass

    if not scores_list:
        return {}

    avg_score = round(sum(scores_list) / len(scores_list))
    total     = len(scores_list)

    if trend_ups > trend_downs * 1.3:
        market_mood = "偏多"
        mood_color  = "#22c55e"
    elif trend_downs > trend_ups * 1.3:
        market_mood = "偏空"
        mood_color  = "#ef4444"
    else:
        market_mood = "震荡"
        mood_color  = "#f5a623"

    return {
        "total_items":    total,
        "avg_score":      avg_score,
        "undervalued":    undervalued,
        "market_mood":    market_mood,
        "mood_color":     mood_color,
        "trend_ups":      trend_ups,
        "trend_downs":    trend_downs,
        "buy_signals":    buy_signals,
        "watch_signals":  watch_signals,
        "active_events":  len(active_events),
    }
