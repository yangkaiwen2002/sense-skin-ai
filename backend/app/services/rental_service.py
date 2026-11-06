from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.item import Item
from app.models.platform import Platform
from app.models.rental_snapshot import RentalSnapshot
from app.schemas.rental import RentVsBuyRequest, RentVsBuyResult
from app.services.market_data import best_quote


def rental_cost(snapshot, days):
    """Weekly blocks plus daily remainder; never assume fractional weekly billing."""
    daily, weekly = snapshot.daily_rental_price, snapshot.weekly_rental_price
    costs = []
    if daily is not None and daily >= 0:
        costs.append(daily * days)
    if weekly is not None and weekly >= 0:
        weeks, remainder = divmod(days, 7)
        costs.append(weekly * (weeks + bool(remainder)))
        if daily is not None and daily >= 0:
            costs.append(weekly * weeks + daily * remainder)
    return round(min(costs), 2) if costs else None


def rent_vs_buy(db: Session, item_id: int, req: RentVsBuyRequest) -> RentVsBuyResult | None:
    item = db.get(Item, item_id)
    if item is None:
        return None
    rows = db.query(RentalSnapshot, Platform).join(Platform).filter(
        RentalSnapshot.item_id == item_id, Platform.supports_rental.is_(True),
        RentalSnapshot.snapshot_time <= datetime.utcnow(),
        RentalSnapshot.snapshot_time >= datetime.utcnow() - timedelta(hours=24),
    ).order_by(RentalSnapshot.snapshot_time.desc(), RentalSnapshot.id.desc()).all()
    latest = {}
    for row, platform in rows:
        latest.setdefault(platform.id, (row, platform))
    options = []
    for row, platform in latest.values():
        cost = rental_cost(row, req.days)
        if row.currency == "CNY" and cost is not None and row.available_count is not None and row.available_count > 0:
            options.append((cost, row, platform))
    # Prefer a provably affordable option; deposit amount is not available in this schema.
    affordable = [o for o in options if not o[1].deposit_required and o[0] <= req.budget]
    rental = min(affordable or options, key=lambda o: (o[0], o[2].id), default=None)
    rent_cost = rental[0] if rental else None
    deposit = bool(rental and rental[1].deposit_required)
    rent_affordable = (None if deposit else rent_cost <= req.budget) if rental else False

    quote = best_quote(db, item_id)
    if quote and datetime.utcnow() - quote.snapshot_time > timedelta(hours=24):
        quote = None
    buy_price = quote.listing_price if quote else None
    buy_affordable = buy_price is not None and buy_price <= req.budget
    # Scenario loss fraction applies to this holding period; it is not a weekly prediction.
    loss = round(buy_price * req.expected_resale_loss_pct, 2) if buy_price is not None else None
    recommendation = "insufficient_data"
    if buy_affordable and rent_affordable:
        recommendation = "rent" if rent_cost < loss else "buy"
    elif rent_affordable:
        recommendation = "rent"
    elif buy_affordable:
        recommendation = "buy"
    elif quote or rental:
        recommendation = "budget_unverified" if deposit and rent_cost <= req.budget else "over_budget"

    explanation = {
        "rent": "在已知预算和报价下，租赁是可行方案；两种方案均可行时按租金与转卖损耗假设比较。",
        "buy": "在已知预算和报价下，购买是可行方案；两种方案均可行时按转卖损耗假设与租金比较。",
        "over_budget": "已知方案均超出预算，暂不建议租赁或购买。",
        "budget_unverified": "租金在预算内，但押金金额未知，无法确认总资金需求。",
        "insufficient_data": "缺少有效购买报价或可用租赁库存，无法给出建议。",
    }[recommendation]
    explanation += " 租赁报价尚未接入实时来源，仅供演示比较。"
    explanation += f" 预算 ¥{req.budget:.2f}；转卖损耗按本次持有期的 {req.expected_resale_loss_pct:.1%} 情景计算，未包含平台手续费及未来价格变化。"
    if deposit:
        explanation += " 租赁需押金，金额待平台确认。"
    return RentVsBuyResult(
        item_id=item_id, item_name=item.item_name, days=req.days,
        rent_cost=rent_cost, rent_available=rental is not None,
        buy_price=buy_price, buy_resale_loss=loss,
        recommendation=recommendation, explanation=explanation,
        rental_platform=rental[2].name if rental else None,
        buy_platform=quote.platform.name if quote else None,
        budget=req.budget, buy_affordable=buy_affordable,
        rent_affordable=rent_affordable, deposit_required=deposit,
    )
