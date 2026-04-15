from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas.item import ItemSearch, ItemBase
from app.services.item_service import search_items, list_items
from app.models.price_snapshot import PriceSnapshot
from app.models.platform import Platform

router = APIRouter(prefix="/items", tags=["items"])


@router.get("")
def get_items(limit: int = 50, db: Session = Depends(get_db)):
    """Return all items with their latest best price."""
    items = list_items(db, limit=limit)

    # For each item, get the latest price snapshot across all platforms
    result = []
    for item in items:
        # Latest snapshot for this item (any platform), ordered by time desc
        row = (
            db.query(PriceSnapshot, Platform.name)
            .join(Platform, PriceSnapshot.platform_id == Platform.id)
            .filter(PriceSnapshot.item_id == item.id)
            .order_by(PriceSnapshot.snapshot_time.desc())
            .first()
        )
        latest, platform_name = (row[0], row[1]) if row else (None, None)
        result.append({
            "id": item.id,
            "item_name": item.item_name,
            "skin_name": item.skin_name,
            "weapon_type": item.weapon_type,
            "rarity": item.rarity,
            "exterior": item.exterior,
            "stattrak": item.stattrak,
            "souvenir": item.souvenir,
            "icon_url": item.icon_url,
            "current_price": latest.listing_price if latest else None,
            "platform": platform_name,
        })
    return result


@router.get("/search")
def search(q: str = "", db: Session = Depends(get_db)):
    if not q:
        items = list_items(db, limit=12)
    else:
        items = search_items(db, q, limit=12)

    result = []
    for item in items:
        row = (
            db.query(PriceSnapshot, Platform.name)
            .join(Platform, PriceSnapshot.platform_id == Platform.id)
            .filter(PriceSnapshot.item_id == item.id)
            .order_by(PriceSnapshot.snapshot_time.desc())
            .first()
        )
        latest, platform_name = (row[0], row[1]) if row else (None, None)
        result.append({
            "id": item.id,
            "item_name": item.item_name,
            "skin_name": item.skin_name,
            "weapon_type": item.weapon_type,
            "rarity": item.rarity,
            "exterior": item.exterior,
            "stattrak": item.stattrak,
            "icon_url": item.icon_url,
            "current_price": latest.listing_price if latest else None,
            "platform": platform_name,
        })
    return result
