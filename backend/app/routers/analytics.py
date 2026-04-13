from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.analytics import ItemOverview, PricePoint, EventAwareAnalysis
from app.services.analytics_service import get_item_overview, get_price_history
from app.services.event_service import get_event_aware_analysis

router = APIRouter(prefix="/items", tags=["analytics"])


@router.get("/{item_id}/overview", response_model=ItemOverview)
def overview(item_id: int, db: Session = Depends(get_db)):
    result = get_item_overview(db, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result


@router.get("/{item_id}/history", response_model=list[PricePoint])
def history(
    item_id: int,
    platform: str | None = Query(None),
    days: int = Query(30),
    db: Session = Depends(get_db),
):
    return get_price_history(db, item_id, platform, days)


@router.get("/{item_id}/event-aware-analysis", response_model=EventAwareAnalysis)
def event_aware(item_id: int, db: Session = Depends(get_db)):
    return get_event_aware_analysis(db, item_id)
