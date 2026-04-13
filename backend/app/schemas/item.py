from pydantic import BaseModel
from datetime import datetime


class ItemSearch(BaseModel):
    id: int
    item_name: str

    model_config = {"from_attributes": True}


class ItemBase(BaseModel):
    id: int
    item_name: str
    weapon_type: str | None = None
    skin_name: str | None = None
    rarity: str | None = None
    exterior: str | None = None
    stattrak: bool = False
    souvenir: bool = False
    category: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
