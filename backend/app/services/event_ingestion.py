"""
Event Ingestion Service
=======================

Loads structured market signals from backend/data/events.json and provides
filtered views by recency, category, and type.

Architecture:
  events.json  →  load_events()  →  get_active_events()/get_events_by_category()
                                      ↓
                              event_mapper.py (per-item relevance)

Future extension points (marked with # FUTURE):
  - fetch_steam_news()   : parse store.steampowered.com/news/app/730
  - fetch_hltv_events()  : scrape hltv.org/events upcoming list
  - fetch_buff_announcements() : BUFF public API or RSS

The contract stays the same regardless of source: each event must conform
to the MarketSignal TypedDict below.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

# ─── Canonical event schema ───────────────────────────────────────────────────
class MarketSignal(TypedDict):
    id:                  str
    title:               str
    event_type:          str          # tournament | update | seasonal | market
    timestamp:           str          # ISO-8601 UTC
    end_timestamp:       str | None
    affected_categories: list[str]   # knife | glove | rifle | sniper | pistol |
                                     # smg | shotgun | all | high_tier | stattrak
    affected_items:      list[str]   # specific item names (partial match)
    impact_direction:    str          # positive | negative | mixed
    impact_strength:     float        # 0.0–1.0
    description:         str
    source:              str
    confidence:          float        # 0.0–1.0


_EVENTS_PATH = Path(__file__).parent.parent.parent / "data" / "events.json"
_cache: list[MarketSignal] | None = None
_cache_loaded_at: datetime | None = None
_CACHE_TTL_SECONDS = 300   # 5-minute in-memory cache


# ─── Core loader ──────────────────────────────────────────────────────────────
def load_events(force_reload: bool = False) -> list[MarketSignal]:
    """Load events from disk (with simple TTL cache)."""
    global _cache, _cache_loaded_at
    now = datetime.now(timezone.utc)

    if (
        not force_reload
        and _cache is not None
        and _cache_loaded_at is not None
        and (now - _cache_loaded_at).total_seconds() < _CACHE_TTL_SECONDS
    ):
        return _cache

    try:
        with open(_EVENTS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        raw = []
    except json.JSONDecodeError as e:
        print(f"[event_ingestion] JSON parse error: {e}")
        raw = []

    _cache = raw
    _cache_loaded_at = now
    return _cache


# ─── FUTURE hook: external sources would feed here ───────────────────────────
def fetch_external_events() -> list[MarketSignal]:
    """
    FUTURE: Fetch from external sources and merge with local events.

    Intended implementations:
      - Steam news API: GET https://store.steampowered.com/events/ajaxgetpartnereventspageable/?appid=730
      - HLTV upcoming events: scrape hltv.org/events?upcoming=1
      - BUFF announcements: monitor buff163.com/notice

    For now, returns empty list (local events.json is the sole source).
    """
    return []


# ─── Filtered views ───────────────────────────────────────────────────────────
def get_active_events(days: int = 90) -> list[MarketSignal]:
    """
    Return events that are active within the given window.
    Includes:
      - Past events within `days` days
      - Upcoming events within 30 days (pre-event speculation window)
    """
    now = datetime.now(timezone.utc)
    cutoff_past     = now.timestamp() - days * 86400
    cutoff_future   = now.timestamp() + 30 * 86400

    events = load_events()
    result = []
    for e in events:
        try:
            ts = datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).timestamp()
        except (ValueError, KeyError):
            continue
        if cutoff_past <= ts <= cutoff_future:
            result.append(e)

    # Sort: upcoming first, then most-recent past
    result.sort(key=lambda e: _parse_ts(e["timestamp"]))
    return result


def get_events_by_category(category: str, days: int = 90) -> list[MarketSignal]:
    """Return active events that include the given category."""
    return [
        e for e in get_active_events(days)
        if category in e.get("affected_categories", []) or "all" in e.get("affected_categories", [])
    ]


def get_events_by_type(event_type: str, days: int = 90) -> list[MarketSignal]:
    """Return active events of a given type (tournament, update, seasonal, market)."""
    return [
        e for e in get_active_events(days)
        if e.get("event_type") == event_type
    ]


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _parse_ts(ts_str: str) -> float:
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def event_days_delta(event: MarketSignal) -> int:
    """
    Days from now to the event timestamp.
    Negative  = event is in the past (e.g., -7 = happened 7 days ago)
    Positive  = event is upcoming   (e.g., +13 = starts in 13 days)
    """
    now_ts  = datetime.now(timezone.utc).timestamp()
    evt_ts  = _parse_ts(event["timestamp"])
    return int((evt_ts - now_ts) / 86400)


def is_event_in_window(event: MarketSignal) -> bool:
    """
    True if the event is currently 'active' in the market-signal sense:
      - tournament: -7 days to end_timestamp (or +14 days if no end)
      - update:     0 to +7 days after patch
      - seasonal:   overlapping with now
      - market:     within 30 days past
    """
    delta = event_days_delta(event)
    etype = event.get("event_type", "")

    if etype == "tournament":
        return -14 <= delta <= 14    # pre-speculation + post-event
    elif etype == "update":
        return -7 <= delta <= 0      # 7 days post-patch
    elif etype == "seasonal":
        # seasonal windows are encoded in timestamp/end_timestamp
        now_ts = datetime.now(timezone.utc).timestamp()
        start  = _parse_ts(event["timestamp"])
        end_ts_str = event.get("end_timestamp")
        end    = _parse_ts(end_ts_str) if end_ts_str else start + 7 * 86400
        return start - 14 * 86400 <= now_ts <= end + 7 * 86400
    else:  # market
        return -30 <= delta <= 0
