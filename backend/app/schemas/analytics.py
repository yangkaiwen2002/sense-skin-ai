from pydantic import BaseModel
from datetime import datetime


class PlatformAnalytics(BaseModel):
    platform: str
    platform_id: int
    current_price: float | None = None
    avg_7d: float | None = None
    avg_30d: float | None = None
    return_7d: float | None = None
    volatility_7d: float | None = None
    spread: float | None = None
    liquidity_score: float | None = None
    risk_labels: list[str] = []


class ItemOverview(BaseModel):
    item_id: int
    item_name: str
    skin_name: str | None = None
    weapon_type: str | None = None
    rarity: str | None = None
    exterior: str | None = None
    stattrak: bool = False
    souvenir: bool = False
    icon_url: str | None = None
    platforms: list[PlatformAnalytics] = []


class PricePoint(BaseModel):
    date: str
    price: float | None = None
    volume: int | None = None


class EventAwareAnalysis(BaseModel):
    is_post_update_window: bool = False
    is_major_window: bool = False
    is_holiday_window: bool = False
    is_tournament_window: bool = False
    is_weekend: bool = False
    has_platform_promo: bool = False
    event_count_last_7d: int = 0
    event_count_last_30d: int = 0
    active_events: list[dict] = []
