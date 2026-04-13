from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.item import ItemSearch
from app.services.item_service import search_items, list_items

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/search", response_model=list[ItemSearch])
def search(q: str = "", db: Session = Depends(get_db)):
    if not q:
        items = list_items(db, limit=20)
    else:
        items = search_items(db, q)
    return [ItemSearch(id=i.id, item_name=i.item_name) for i in items]
