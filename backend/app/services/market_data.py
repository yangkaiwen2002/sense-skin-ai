"""Shared quote selection and UTC daily analytics for irregular snapshots.

One observation per UTC date (the last valid quote) prevents polling frequency
from changing daily averages. Missing days are never forward-filled.
"""
from datetime import datetime, timedelta
from math import isfinite

from sqlalchemy.orm import Session

from app.models.price_snapshot import PriceSnapshot
from app.utils.metrics import compute_liquidity_score


def valid_price(value):
    return value is not None and isfinite(value) and value > 0


def latest_quotes(db: Session, item_id: int) -> list[PriceSnapshot]:
    rows = db.query(PriceSnapshot).filter(
        PriceSnapshot.item_id == item_id,
        PriceSnapshot.snapshot_time <= datetime.utcnow(),
    ).order_by(PriceSnapshot.snapshot_time.desc(), PriceSnapshot.id.desc()).all()
    # Select latest first, then validate: don't resurrect an older unavailable quote.
    latest = {}
    for row in rows:
        latest.setdefault(row.platform_id, row)
    valid = [s for s in latest.values() if s.currency == "CNY" and valid_price(s.listing_price)]
    observed = [s for s in valid if s.price_kind == "observed"]
    return observed or valid


def best_quote(db: Session, item_id: int):
    return min(latest_quotes(db, item_id), key=lambda s: (datetime.utcnow() - s.snapshot_time > timedelta(hours=24), s.listing_price, s.platform_id), default=None)


def summarize_snapshots(snapshots, now=None):
    now = now or datetime.utcnow()
    rows = sorted((s for s in snapshots if s.snapshot_time <= now and s.currency == "CNY"),
                  key=lambda s: (s.snapshot_time, s.id or 0))
    if not rows:
        return None
    current = rows[-1]
    rows = [s for s in rows if s.price_kind == current.price_kind and s.source == current.source]
    daily = {}
    for row in rows:
        daily[row.snapshot_time.date()] = row
    daily = {day: row for day, row in daily.items() if valid_price(row.listing_price)}
    today = now.date()

    def window(days):
        return [row for day, row in daily.items() if today - timedelta(days=days - 1) <= day <= today]

    def average(rows, field):
        values = [getattr(row, field) for row in rows if getattr(row, field) is not None]
        return round(sum(values) / len(values), 2) if values else None

    week, month = window(7), window(30)
    baseline = daily.get(today - timedelta(days=7))
    price = current.listing_price if valid_price(current.listing_price) else None
    # Require both endpoints; a two-hour history is not a seven-day return.
    ret = None
    if price is not None and baseline and current.snapshot_time.date() == today:
        ret = round((price - baseline.listing_price) / baseline.listing_price, 4)
    # Only adjacent calendar dates contribute daily returns, never gap-spanning changes.
    week_with_baseline = [daily[d] for d in sorted(daily) if today - timedelta(days=7) <= d <= today]
    returns = [b.listing_price / a.listing_price - 1 for a, b in zip(week_with_baseline, week_with_baseline[1:])
               if (b.snapshot_time.date() - a.snapshot_time.date()).days == 1]
    volatility = None
    if len(returns) >= 2:
        mean = sum(returns) / len(returns)
        volatility = round((sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)) ** 0.5, 4)
    return {
        "current_price": price,
        "avg_7d": average(week, "listing_price"),
        "avg_30d": average(month, "listing_price"),
        "return_7d": ret,
        "volatility_7d": volatility,
        "spread": current.spread,
        "liquidity_score": compute_liquidity_score(
            average(week, "volume_24h"), average(week, "liquidity_depth"), current.spread, price),
        "snapshot_time": current.snapshot_time,
        "source": current.source,
        "price_kind": current.price_kind,
        "is_stale": now - current.snapshot_time > timedelta(hours=24),
        "observed_days_30d": len(month),
    }
