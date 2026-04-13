from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.schemas.comparison import ComparisonResult, PlatformComparison
from app.utils.metrics import compute_avg, compute_liquidity_score


def get_comparison(db: Session, item_id: int) -> ComparisonResult | None:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    platforms = db.query(Platform).all()
    comparisons = []

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
        volumes = [s.volume_24h for s in snapshots[-7:] if s.volume_24h is not None]
        depths = [s.liquidity_depth for s in snapshots[-7:] if s.liquidity_depth is not None]
        avg_volume = sum(volumes) / len(volumes) if volumes else None
        avg_depth = sum(depths) / len(depths) if depths else None

        comparisons.append(
            PlatformComparison(
                platform=platform.name,
                platform_id=platform.id,
                supports_rental=platform.supports_rental,
                current_price=current.listing_price,
                avg_7d=compute_avg(prices, 7),
                avg_30d=compute_avg(prices, 30),
                spread=current.spread,
                liquidity_score=compute_liquidity_score(avg_volume, avg_depth, current.spread, current.listing_price),
            )
        )

    if not comparisons:
        return ComparisonResult(item_id=item_id, item_name=item.item_name)

    valid = [c for c in comparisons if c.current_price is not None]
    if valid:
        best = min(valid, key=lambda c: c.current_price)
        best_price = best.current_price
        best_name = best.platform
        for c in comparisons:
            c.is_best_price = c.platform == best_name
            if c.current_price is not None and best_price and best_price > 0:
                c.price_vs_best_pct = round((c.current_price - best_price) / best_price * 100, 2)
    else:
        best_name = None

    return ComparisonResult(
        item_id=item_id,
        item_name=item.item_name,
        best_platform=best_name,
        platforms=comparisons,
    )
