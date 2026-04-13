from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.rental import RentVsBuyRequest, RentVsBuyResult
from app.services.rental_service import rent_vs_buy

router = APIRouter(prefix="/items", tags=["rental"])


@router.post("/{item_id}/rent-vs-buy", response_model=RentVsBuyResult)
def rent_vs_buy_endpoint(
    item_id: int, req: RentVsBuyRequest, db: Session = Depends(get_db)
):
    result = rent_vs_buy(db, item_id, req)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
