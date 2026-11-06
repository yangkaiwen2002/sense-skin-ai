from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.item_service import search_items, list_items
from app.services.market_data import best_quote

router = APIRouter(prefix="/items", tags=["items"])


@router.get("")
def get_items(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """Return all items with their latest best price."""
    items = list_items(db, limit=limit)

    # For each item, get the latest price snapshot across all platforms
    result = []
    for item in items:
        latest = best_quote(db, item.id)
        platform_name = latest.platform.name if latest else None
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
            "snapshot_time": latest.snapshot_time if latest else None,
            "source": latest.source if latest else None,
            "price_kind": latest.price_kind if latest else None,
            "is_stale": bool(latest and datetime.utcnow() - latest.snapshot_time > timedelta(hours=24)),
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
        latest = best_quote(db, item.id)
        platform_name = latest.platform.name if latest else None
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
            "snapshot_time": latest.snapshot_time if latest else None,
            "source": latest.source if latest else None,
            "price_kind": latest.price_kind if latest else None,
            "is_stale": bool(latest and datetime.utcnow() - latest.snapshot_time > timedelta(hours=24)),
        })
    return result
