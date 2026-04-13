from datetime import datetime, timedelta
from typing import Any


def check_event_windows(events: list[Any], reference_date: datetime | None = None) -> dict:
    now = reference_date or datetime.utcnow()
    today = now.date()

    is_post_update = False
    is_major = False
    is_holiday = False
    has_promo = False
    is_tournament = False
    active_events = []

    for event in events:
        event_date = event.event_date.date() if hasattr(event.event_date, "date") else event.event_date
        days_diff = (today - event_date).days

        if event.event_type == "game_update":
            if 0 <= days_diff <= 3:
                is_post_update = True
                active_events.append({"type": event.event_type, "title": event.title, "days_ago": days_diff})

        elif event.event_type == "major_event":
            if -7 <= days_diff <= 10:
                is_major = True
                active_events.append({"type": event.event_type, "title": event.title, "days_ago": days_diff})

        elif event.event_type == "holiday":
            if -3 <= days_diff <= 2:
                is_holiday = True
                active_events.append({"type": event.event_type, "title": event.title, "days_ago": days_diff})

        elif event.event_type == "platform_promo":
            if -7 <= days_diff <= 0:
                has_promo = True
                active_events.append({"type": event.event_type, "title": event.title, "days_ago": days_diff})

        elif event.event_type == "tournament":
            # Tournament window: -14 days pre (speculation) to +7 days post (sticker capsule release)
            if -14 <= days_diff <= 7:
                is_tournament = True
                active_events.append({"type": event.event_type, "title": event.title, "days_ago": days_diff,
                                      "source": getattr(event, "source", None)})

    return {
        "is_post_update_window": is_post_update,
        "is_major_window": is_major,
        "is_holiday_window": is_holiday,
        "is_tournament_window": is_tournament,
        "is_weekend": today.weekday() >= 5,
        "has_platform_promo": has_promo,
        "active_events": active_events,
    }
