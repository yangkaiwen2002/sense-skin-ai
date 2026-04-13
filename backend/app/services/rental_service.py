from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.price_snapshot import PriceSnapshot
from app.models.rental_snapshot import RentalSnapshot
from app.schemas.rental import RentVsBuyRequest, RentVsBuyResult


def rent_vs_buy(db: Session, item_id: int, req: RentVsBuyRequest) -> RentVsBuyResult | None:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return None

    rental_platforms = db.query(Platform).filter(Platform.supports_rental == True).all()
    rental_platform_ids = [p.id for p in rental_platforms]

    latest_rental = (
        db.query(RentalSnapshot)
        .filter(
            RentalSnapshot.item_id == item_id,
            RentalSnapshot.platform_id.in_(rental_platform_ids),
        )
        .order_by(RentalSnapshot.snapshot_time.desc())
        .first()
    )

    buy_snapshot = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.item_id == item_id)
        .order_by(PriceSnapshot.snapshot_time.desc())
        .first()
    )

    buy_price = buy_snapshot.listing_price if buy_snapshot else None
    buy_resale_loss = None
    if buy_price is not None:
        buy_resale_loss = round(buy_price * req.expected_resale_loss_pct * req.days / 7, 2)

    rent_cost = None
    rent_available = False
    rental_platform_name = None

    if latest_rental:
        rent_available = True
        rental_platform = db.query(Platform).filter(Platform.id == latest_rental.platform_id).first()
        rental_platform_name = rental_platform.name if rental_platform else None

        if req.days <= 7 and latest_rental.daily_rental_price:
            rent_cost = round(latest_rental.daily_rental_price * req.days, 2)
        elif latest_rental.weekly_rental_price:
            weeks = req.days / 7
            rent_cost = round(latest_rental.weekly_rental_price * weeks, 2)
        elif latest_rental.daily_rental_price:
            rent_cost = round(latest_rental.daily_rental_price * req.days, 2)

    recommendation = "insufficient_data"
    explanation = "数据不足，无法给出建议。"

    if rent_cost is not None and buy_resale_loss is not None:
        if rent_cost < buy_resale_loss:
            recommendation = "rent"
            explanation = (
                f"租赁 {req.days} 天的成本约为 ¥{rent_cost:.2f}，"
                f"而购买后转卖预计损耗约 ¥{buy_resale_loss:.2f}。"
                f"短期使用建议选择租赁，更为划算。"
            )
        else:
            recommendation = "buy"
            explanation = (
                f"购买后转卖预计损耗约 ¥{buy_resale_loss:.2f}，"
                f"低于或接近租赁成本 ¥{rent_cost:.2f}。"
                f"如果你有长期使用需求，购买更合算。"
            )
    elif not rent_available:
        recommendation = "buy"
        explanation = "当前无可用租赁，建议直接购买。"

    buy_platform_snapshot = (
        db.query(PriceSnapshot, Platform)
        .join(Platform, PriceSnapshot.platform_id == Platform.id)
        .filter(PriceSnapshot.item_id == item_id)
        .order_by(PriceSnapshot.snapshot_time.desc())
        .first()
    )
    buy_platform_name = buy_platform_snapshot[1].name if buy_platform_snapshot else None

    return RentVsBuyResult(
        item_id=item_id,
        item_name=item.item_name,
        days=req.days,
        rent_cost=rent_cost,
        rent_available=rent_available,
        buy_price=buy_price,
        buy_resale_loss=buy_resale_loss,
        recommendation=recommendation,
        explanation=explanation,
        rental_platform=rental_platform_name,
        buy_platform=buy_platform_name,
    )
