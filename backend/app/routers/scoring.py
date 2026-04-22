from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.item import Item
from app.services.scoring import score_item, score_item_dict
from app.services.event_ingestion import get_active_events, event_days_delta
from app.services.event_mapper import map_events_to_item
from app.services.decision_engine import decide, decision_to_dict
from app.services.opportunity_detector import detect_opportunities, get_market_summary

router = APIRouter(tags=["scoring"])


@router.get("/items/{item_id}/score")
def get_item_score(item_id: int, db: Session = Depends(get_db)):
    """
    Return the full AI score breakdown for a single item, including:
    - total_score (0–100)
    - subscores (rarity, exterior, liquidity, trend, valuation, demand)
    - valuation_label (低估 / 合理 / 高估)
    - confidence
    - reasons_to_buy
    - risks
    """
    result = score_item_dict(db, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found or insufficient data")
    return result


@router.get("/items/{item_id}/decision")
def get_item_decision(item_id: int, db: Session = Depends(get_db)):
    """
    Full decision pipeline for a single item:
      events.json → event_ingestion → event_mapper → scoring (event-aware) → decision_engine
    Returns a DecisionResult with BUY/WATCH/HOLD/AVOID recommendation and full evidence chain.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Load and map events
    events    = get_active_events(days=90)
    event_map = map_events_to_item(item, events)

    # Score with event context
    score = score_item(db, item_id, event_map=event_map)
    if score is None:
        raise HTTPException(status_code=404, detail="Insufficient price data for scoring")

    # Synthesise decision
    result = decide(item, score, event_map)
    return decision_to_dict(result)


@router.get("/opportunities")
def get_opportunities(limit: int = 8, db: Session = Depends(get_db)):
    """
    Scan all items and return the top `limit` investment opportunities.
    Sorted by total_score DESC.
    """
    items = detect_opportunities(db, limit=limit)
    return {"opportunities": items, "count": len(items)}


@router.get("/market-summary")
def get_market_summary_endpoint(db: Session = Depends(get_db)):
    """
    Aggregate market-level signals: avg score, mood, undervalued count.
    Used by the Home dashboard signal bar.
    """
    return get_market_summary(db)


@router.get("/market/events")
def get_market_events():
    """
    Return active market events (past 90 days + upcoming 30 days) formatted for UI display.
    Includes tournament countdowns, patch notes, seasonal events.
    """
    events = get_active_events(days=90)
    now = datetime.now(timezone.utc)

    result = []
    for evt in events:
        delta = event_days_delta(evt)

        # Classify timing
        if delta > 0:
            if delta <= 7:
                timing_label = f"{delta}天后开始"
                timing_class = "imminent"
            elif delta <= 14:
                timing_label = f"{delta}天后开始"
                timing_class = "upcoming"
            else:
                timing_label = f"{delta}天后开始"
                timing_class = "future"
        elif delta >= -3:
            timing_label = "进行中"
            timing_class = "active"
        elif delta >= -14:
            timing_label = f"{abs(delta)}天前结束"
            timing_class = "recent"
        else:
            timing_label = f"{abs(delta)}天前"
            timing_class = "historical"

        type_color = {
            "tournament": "#4a8ef5",
            "update":     "#8b5cf6",
            "seasonal":   "#f5a623",
            "market":     "#22c55e",
        }.get(evt.get("event_type", ""), "#5e98d9")

        direction_color = {
            "positive": "#22c55e",
            "negative": "#ef4444",
            "mixed":    "#f5a623",
        }.get(evt.get("impact_direction", ""), "#5e98d9")

        result.append({
            "id":               evt["id"],
            "title":            evt["title"],
            "event_type":       evt.get("event_type", ""),
            "type_color":       type_color,
            "days_delta":       delta,
            "timing_label":     timing_label,
            "timing_class":     timing_class,
            "impact_direction": evt.get("impact_direction", ""),
            "direction_color":  direction_color,
            "impact_strength":  evt.get("impact_strength", 0),
            "description":      evt.get("description", "")[:200],
            "source":           evt.get("source", ""),
            "confidence":       evt.get("confidence", 0),
        })

    # Sort: active/imminent first, then upcoming, then historical
    priority = {"active": 0, "imminent": 1, "upcoming": 2, "future": 3, "recent": 4, "historical": 5}
    result.sort(key=lambda e: (priority.get(e["timing_class"], 9), e["days_delta"] if e["days_delta"] > 0 else -e["days_delta"]))

    return {"events": result, "count": len(result)}
