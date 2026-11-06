from datetime import datetime
from pydantic import BaseModel


class PlatformComparison(BaseModel):
    platform: str
    platform_id: int
    supports_rental: bool = False
    current_price: float | None = None
    snapshot_time: datetime | None = None
    is_stale: bool = False
    source: str = "unknown"
    price_kind: str = "legacy_unknown"
    observed_days_30d: int = 0
    avg_7d: float | None = None
    avg_30d: float | None = None
    spread: float | None = None
    liquidity_score: float | None = None
    price_vs_best_pct: float | None = None
    is_best_price: bool = False


class ComparisonResult(BaseModel):
    item_id: int
    item_name: str
    best_platform: str | None = None
    platforms: list[PlatformComparison] = []
