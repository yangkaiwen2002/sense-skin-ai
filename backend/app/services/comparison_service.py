from sqlalchemy.orm import Session

from app.models.platform import Platform
from app.schemas.comparison import ComparisonResult, PlatformComparison
from app.services.analytics_service import get_item_overview


def get_comparison(db: Session, item_id: int) -> ComparisonResult | None:
    overview = get_item_overview(db, item_id)
    if overview is None:
        return None
    rental = {p.id: p.supports_rental for p in db.query(Platform).all()}
    comparisons = [PlatformComparison(
        **p.model_dump(), supports_rental=rental.get(p.platform_id, False)
    ) for p in overview.platforms]
    valid = [p for p in comparisons if p.current_price is not None and not p.is_stale]
    best = min(valid, key=lambda p: p.current_price, default=None)
    for p in comparisons:
        p.is_best_price = bool(best and not p.is_stale and p.current_price == best.current_price)
        if best and not p.is_stale and p.current_price is not None:
            p.price_vs_best_pct = round((p.current_price - best.current_price) / best.current_price * 100, 2)
    return ComparisonResult(item_id=item_id, item_name=overview.item_name,
                            best_platform=best.platform if best else None, platforms=comparisons)
