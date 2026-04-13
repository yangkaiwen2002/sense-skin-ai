from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.schemas.analytics import PlatformAnalytics, ItemOverview, PricePoint
from app.utils.metrics import compute_avg, compute_return, compute_volatility, compute_liquidity_score
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

        prices = [s.listing_price for s in snapshots if s.listing_price is not None]
        if not prices:
            continue

        current = snapshots[-1]
        current_price = current.listing_price
        avg_7d = compute_avg(prices, 7)
        avg_30d = compute_avg(prices, 30)
        return_7d = compute_return(prices, 7)
        volatility_7d = compute_volatility(prices[-30:])

        volumes = [s.volume_24h for s in snapshots[-7:] if s.volume_24h is not None]
        depths = [s.liquidity_depth for s in snapshots[-7:] if s.liquidity_depth is not None]
        avg_volume = sum(volumes) / len(volumes) if volumes else None
        avg_depth = sum(depths) / len(depths) if depths else None
        spread = current.spread

        liquidity_score = compute_liquidity_score(avg_volume, avg_depth, spread, current_price)
        risk_labels = compute_risk_labels(volatility_7d, liquidity_score, current_price, avg_30d)

        platform_analytics.append(
            PlatformAnalytics(
                platform=platform.name,
                platform_id=platform.id,
                current_price=current_price,
                avg_7d=avg_7d,
                avg_30d=avg_30d,
                return_7d=return_7d,
                volatility_7d=volatility_7d,
                spread=spread,
                liquidity_score=liquidity_score,
                risk_labels=risk_labels,
            )
        )

    return ItemOverview(
        item_id=item.id,
        item_name=item.item_name,
        weapon_type=item.weapon_type,
        rarity=item.rarity,
        exterior=item.exterior,
        stattrak=item.stattrak,
        souvenir=item.souvenir,
        platforms=platform_analytics,
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
        if platform:
            query = query.filter(PriceSnapshot.platform_id == platform.id)

    snapshots = query.order_by(PriceSnapshot.snapshot_time.asc()).all()

    return [
        PricePoint(
            date=s.snapshot_time.strftime("%Y-%m-%d"),
            price=s.listing_price,
            volume=s.volume_24h,
        )
        for s in snapshots
    ]
