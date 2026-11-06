from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.schemas.analytics import PlatformAnalytics, ItemOverview, PricePoint
from app.services.market_data import summarize_snapshots
from app.utils.risk_rules import compute_risk_labels


def get_item_overview(db: Session, item_id: int) -> ItemOverview | None:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    platforms = db.query(Platform).all()
    platform_analytics = []

    for platform in platforms:
        snapshots = (
            db.query(PriceSnapshot)
            .filter(
                PriceSnapshot.item_id == item_id,
                PriceSnapshot.platform_id == platform.id,
            )
            .order_by(PriceSnapshot.snapshot_time.asc())
            .all()
        )

        if not snapshots:
            continue

        metrics = summarize_snapshots(snapshots)
        if metrics is None:
            continue
        risk_labels = compute_risk_labels(metrics["volatility_7d"], metrics["liquidity_score"],
                                         metrics["current_price"], metrics["avg_30d"])
        if metrics["is_stale"]:
            risk_labels.append("报价超过24小时未更新")

        platform_analytics.append(
            PlatformAnalytics(
                platform=platform.name,
                platform_id=platform.id,
                **metrics,
                risk_labels=risk_labels,
            )
        )

    observed = [p for p in platform_analytics if p.price_kind == "observed"]
    platform_analytics = observed or platform_analytics
    return ItemOverview(
        item_id=item.id,
        item_name=item.item_name,
        skin_name=item.skin_name,
        weapon_type=item.weapon_type,
        rarity=item.rarity,
        exterior=item.exterior,
        stattrak=item.stattrak,
        souvenir=item.souvenir,
        icon_url=item.icon_url,
        platforms=sorted(platform_analytics, key=lambda p: (p.current_price is None, p.is_stale, p.current_price or 0, p.platform_id)),
    )


def get_price_history(
    db: Session, item_id: int, platform_name: str | None = None, days: int = 30
) -> list[PricePoint]:
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(PriceSnapshot).filter(
        PriceSnapshot.item_id == item_id,
        PriceSnapshot.snapshot_time >= since,
    )

    if platform_name:
        platform = db.query(Platform).filter(Platform.name.ilike(platform_name)).first()
        if not platform:
            return []
        query = query.filter(PriceSnapshot.platform_id == platform.id)

    else:
        from app.services.market_data import best_quote
        quote = best_quote(db, item_id)
        if quote is None:
            return []
        query = query.filter(PriceSnapshot.platform_id == quote.platform_id)

    query = query.filter(PriceSnapshot.snapshot_time <= datetime.utcnow())
    snapshots = query.order_by(PriceSnapshot.snapshot_time.asc(), PriceSnapshot.id.asc()).all()

    if snapshots:
        latest = snapshots[-1]
        snapshots = [s for s in snapshots if s.price_kind == latest.price_kind and s.source == latest.source]
    daily = {}
    for snapshot in snapshots:
        daily[snapshot.snapshot_time.date()] = snapshot
    return [
        PricePoint(
            date=s.snapshot_time.strftime("%Y-%m-%d"),
            price=s.listing_price,
            volume=s.volume_24h,
        )
        for s in daily.values()
    ]
