from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.item import Item


def search_items(db: Session, q: str, limit: int = 20) -> list[Item]:
    return (
        db.query(Item)
        .filter(or_(
            Item.item_name.ilike(f"%{q}%"),
            Item.skin_name.ilike(f"%{q}%"),
            Item.weapon_type.ilike(f"%{q}%"),
        ))
        .limit(limit)
        .all()
    )


def get_item(db: Session, item_id: int) -> Item | None:
    return db.query(Item).filter(Item.id == item_id).first()


def list_items(db: Session, limit: int = 50) -> list[Item]:
    return db.query(Item).limit(limit).all()
