from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.report import EventSchema, AIReportResponse
from app.services.event_service import get_events_for_item
from app.services.ai_report_service import generate_ai_report

router = APIRouter(prefix="/items", tags=["reports"])


@router.get("/{item_id}/events", response_model=list[EventSchema])
def events(item_id: int, days: int = Query(30), db: Session = Depends(get_db)):
    return get_events_for_item(db, item_id, days)


@router.post("/{item_id}/ai-report", response_model=AIReportResponse)
def ai_report(item_id: int, db: Session = Depends(get_db)):
    result = generate_ai_report(db, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
