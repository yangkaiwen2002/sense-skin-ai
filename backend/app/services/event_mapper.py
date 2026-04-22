"""
Event Mapper
============

Maps structured market signals to a specific Item and produces a scored
EventMapping result that the scoring engine and decision engine consume.

Pipeline:
  Item attributes  ──────────────────────────────────────────────┐
                                                                  ↓
  events.json → event_ingestion.get_active_events() → map_events_to_item()
                                                                  ↓
                                                         EventMapping
                                                   (event_impact_score,
                                                    event_signal_score,
                                                    relevant_events,
                                                    event_summary)

Relevance scoring rules
-----------------------
  Base relevance  = category_match_score × recency_weight × event.impact_strength × event.confidence

  category_match_score:
    "all" match         = 1.0
    weapon_type match   = 0.90
    rarity tier match   = 0.80
    stattrak match      = 0.75
    specific item name  = 1.0 (override, highest priority)

  recency_weight (signed — positive for past, negative for future):
    upcoming 0–7 days   = 0.90  (pre-event speculation already priced in)
    upcoming 7–14 days  = 1.00  (prime pre-event window)
    upcoming 14–30 days = 0.60
    past 0–7 days       = 1.00  (post-event peak)
    past 7–30 days      = 0.55
    past 30–60 days     = 0.25
    past 60–90 days     = 0.10
    outside window      = 0.0

  Final event_impact_score: sum of (relevance × direction_sign) clamped to [-1.0, +1.0]
  event_signal_score (0–100): 50 + event_impact_score × 40
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.models.item import Item
from app.services.event_ingestion import (
    MarketSignal,
    get_active_events,
    event_days_delta,
)

# ─── Category → weapon_type mapping ──────────────────────────────────────────
_CATEGORY_TO_WEAPON = {
    "knife":   {"刀"},
    "glove":   {"手套"},
    "rifle":   {"步枪"},
    "sniper":  {"狙击枪"},
    "pistol":  {"手枪"},
    "smg":     {"冲锋枪"},
    "shotgun": {"霰弹枪"},
    "heavy":   {"霰弹枪", "机枪"},
    "all":     {"刀", "手套", "步枪", "狙击枪", "手枪", "冲锋枪", "霰弹枪", "机枪"},
}

_HIGH_TIER_RARITIES = {"违禁", "隐秘", "保密"}


# ─── Output types ─────────────────────────────────────────────────────────────

@dataclass
class EventSignal:
    event_id:         str
    title:            str
    event_type:       str
    days_delta:       int          # negative = past, positive = upcoming
    relevance:        float        # 0–1 how relevant to this item
    impact_direction: str          # positive | negative | mixed
    impact_strength:  float        # 0–1 from events.json
    window_label:     str          # "pre-event" | "active" | "post-event" | "historical"
    contribution:     float        # signed contribution to event_impact_score
    source:           str
    description:      str


@dataclass
class EventMapping:
    relevant_events:    list[EventSignal] = field(default_factory=list)
    event_impact_score: float = 0.0   # -1.0 to +1.0
    event_signal_score: int   = 50    # 0–100 (50 = neutral)
    event_summary:      str   = ""
    confidence:         float = 0.5


# ─── Core mapping function ────────────────────────────────────────────────────

def map_events_to_item(item: Item, events: list[MarketSignal] | None = None) -> EventMapping:
    """
    Given an Item, find all relevant active events, score their relevance,
    and return an EventMapping that can be fed into the scoring and decision engines.
    """
    if events is None:
        events = get_active_events(days=90)

    signals: list[EventSignal] = []

    for evt in events:
        delta     = event_days_delta(evt)
        rec_w     = _recency_weight(delta, evt["event_type"])
        if rec_w == 0.0:
            continue

        cat_score = _category_match(item, evt)
        if cat_score == 0.0:
            continue

        base_relevance = cat_score * rec_w * evt["impact_strength"] * evt["confidence"]
        direction_sign = _direction_sign(evt["impact_direction"])
        contribution   = base_relevance * direction_sign

        signals.append(EventSignal(
            event_id         = evt["id"],
            title            = evt["title"],
            event_type       = evt["event_type"],
            days_delta       = delta,
            relevance        = round(base_relevance, 3),
            impact_direction = evt["impact_direction"],
            impact_strength  = evt["impact_strength"],
            window_label     = _window_label(delta, evt["event_type"]),
            contribution     = round(contribution, 3),
            source           = evt.get("source", ""),
            description      = evt.get("description", ""),
        ))

    # Sort by absolute contribution descending (most impactful first)
    signals.sort(key=lambda s: abs(s.contribution), reverse=True)

    # Aggregate impact — sum contributions, clamp to [-1, 1]
    total_impact = sum(s.contribution for s in signals)
    total_impact = max(-1.0, min(1.0, total_impact))

    # Convert to 0-100 score: 0 → 10, neutral → 50, +1 → 90
    signal_score = int(50 + total_impact * 40)
    signal_score = max(10, min(90, signal_score))

    # Confidence scales with number of relevant signals and their quality
    if signals:
        avg_relevance = sum(s.relevance for s in signals) / len(signals)
        confidence = round(min(0.95, 0.45 + avg_relevance * 0.6 + len(signals) * 0.02), 2)
    else:
        confidence = 0.40

    summary = _build_summary(item, signals, total_impact)

    return EventMapping(
        relevant_events    = signals[:8],   # cap for API response size
        event_impact_score = round(total_impact, 3),
        event_signal_score = signal_score,
        event_summary      = summary,
        confidence         = confidence,
    )


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _category_match(item: Item, evt: MarketSignal) -> float:
    """Return 0.0 if event is not relevant to this item, else 0.75–1.0."""
    cats = set(evt.get("affected_categories", []))
    item_weapon = item.weapon_type or ""
    item_rarity = item.rarity or ""

    best = 0.0

    # Specific item name match (highest priority)
    for name_fragment in evt.get("affected_items", []):
        if name_fragment.lower() in (item.item_name or "").lower():
            best = max(best, 1.0)

    # "all" category
    if "all" in cats:
        best = max(best, 0.80)

    # Weapon-type category match
    for cat, weapons in _CATEGORY_TO_WEAPON.items():
        if cat in cats and item_weapon in weapons:
            best = max(best, 0.92)

    # High-tier rarity match
    if "high_tier" in cats and item_rarity in _HIGH_TIER_RARITIES:
        best = max(best, 0.82)

    # StatTrak match
    if "stattrak" in cats and item.stattrak:
        best = max(best, 0.78)

    return best


def _recency_weight(days_delta: int, event_type: str) -> float:
    """
    Compute a recency weight based on how far the event is from today.
    days_delta: positive = upcoming, negative = past
    """
    d = days_delta  # positive = future, negative = past

    if d > 0:  # upcoming event
        if   d <= 7:   return 0.90   # imminent speculation
        elif d <= 14:  return 1.00   # prime pre-event window
        elif d <= 30:  return 0.55
        else:          return 0.0
    else:  # past event (d is negative or 0)
        age = abs(d)
        if event_type == "tournament":
            # Tournaments have longer tail
            if   age <= 7:   return 0.95
            elif age <= 21:  return 0.60
            elif age <= 45:  return 0.30
            else:            return 0.10 if age <= 90 else 0.0
        elif event_type == "update":
            if   age <= 7:   return 1.00
            elif age <= 14:  return 0.50
            else:            return 0.0
        elif event_type == "seasonal":
            if   age <= 14:  return 0.80
            elif age <= 30:  return 0.40
            else:            return 0.05 if age <= 90 else 0.0
        else:  # market
            if   age <= 14:  return 0.90
            elif age <= 30:  return 0.50
            elif age <= 60:  return 0.20
            else:            return 0.0


def _direction_sign(direction: str) -> float:
    if direction == "positive": return  1.0
    if direction == "negative": return -1.0
    return 0.2   # "mixed" — small positive tilt (markets generally react)


def _window_label(days_delta: int, event_type: str) -> str:
    if days_delta > 0:
        return f"pre-event ({days_delta}天后)"
    elif days_delta >= -3:
        return "active"
    elif days_delta >= -14:
        return "post-event"
    else:
        return "historical"


def _build_summary(item: Item, signals: list[EventSignal], total_impact: float) -> str:
    if not signals:
        return "当前无明显市场事件影响此饰品"

    top = signals[0]

    if total_impact > 0.5:
        mood = "强正面催化"
    elif total_impact > 0.2:
        mood = "温和正面支撑"
    elif total_impact > -0.1:
        mood = "中性偏稳"
    elif total_impact > -0.3:
        mood = "温和负面压力"
    else:
        mood = "明显下行压力"

    # Build natural summary
    if top.days_delta > 0:
        timing = f"《{top.title}》将于 {top.days_delta} 天后开始"
    elif top.days_delta >= -7:
        timing = f"《{top.title}》近期结束"
    else:
        timing = f"《{top.title}》({abs(top.days_delta)} 天前)"

    category_note = ""
    if item.weapon_type in ("刀", "手套") and total_impact > 0.1:
        category_note = f"；{item.weapon_type}类在此类事件中通常有更强反应"
    elif item.stattrak and total_impact > 0:
        category_note = "；StatTrak™ 版本在赛事期间吸引额外收藏关注"

    return f"{timing}，当前市场情绪 {mood}{category_note}（综合 {len(signals)} 个信号）"
