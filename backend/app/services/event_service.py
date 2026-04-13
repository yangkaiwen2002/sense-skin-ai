from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.market_event import MarketEvent, EventTag
from app.schemas.analytics import EventAwareAnalysis
from app.schemas.report import EventSchema
from app.utils.event_rules import check_event_windows


def get_events(db: Session, days: int = 60) -> list[MarketEvent]:
    since = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(MarketEvent)
        .filter(MarketEvent.event_date >= since)
        .order_by(MarketEvent.event_date.desc())
        .all()
    )


def get_events_for_item(db: Session, item_id: int, days: int = 30) -> list[EventSchema]:
    since = datetime.utcnow() - timedelta(days=days)
    events = (
        db.query(MarketEvent)
        .filter(MarketEvent.event_date >= since)
        .order_by(MarketEvent.event_date.desc())
        .all()
    )

    result = []
    for e in events:
        tags = [t.tag for t in e.tags]
        result.append(
            EventSchema(
                id=e.id,
                event_date=e.event_date.strftime("%Y-%m-%d"),
                event_type=e.event_type,
                title=e.title,
                summary=e.summary,
                impact_scope=e.impact_scope,
                region=e.region,
                tags=tags,
            )
        )
    return result


def get_event_aware_analysis(db: Session, item_id: int) -> EventAwareAnalysis:
    since = datetime.utcnow() - timedelta(days=60)
    events = (
        db.query(MarketEvent)
        .filter(MarketEvent.event_date >= since)
        .order_by(MarketEvent.event_date.asc())
        .all()
    )

    windows = check_event_windows(events)

    now = datetime.utcnow()
    last_7d = datetime.utcnow() - timedelta(days=7)
    last_30d = datetime.utcnow() - timedelta(days=30)

    count_7d = sum(1 for e in events if e.event_date >= last_7d)
    count_30d = sum(1 for e in events if e.event_date >= last_30d)

    return EventAwareAnalysis(
        is_post_update_window=windows["is_post_update_window"],
        is_major_window=windows["is_major_window"],
        is_holiday_window=windows["is_holiday_window"],
        is_tournament_window=windows["is_tournament_window"],
        is_weekend=windows["is_weekend"],
        has_platform_promo=windows["has_platform_promo"],
        event_count_last_7d=count_7d,
        event_count_last_30d=count_30d,
        active_events=windows["active_events"],
    )
