from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.comparison import ComparisonResult
from app.services.comparison_service import get_comparison

router = APIRouter(prefix="/items", tags=["compare"])


@router.get("/{item_id}/compare", response_model=ComparisonResult)
def compare(item_id: int, db: Session = Depends(get_db)):
    result = get_comparison(db, item_id)
    if not result:
        raise HTTPException(status_code=404, detail="Item not found")
    return result
