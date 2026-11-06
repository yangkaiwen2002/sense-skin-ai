from pydantic import BaseModel, Field


class RentVsBuyRequest(BaseModel):
    days: int = Field(7, ge=1, le=365)
    budget: float = Field(500.0, ge=0, allow_inf_nan=False)
    expected_resale_loss_pct: float = Field(0.04, ge=0, le=1, allow_inf_nan=False)


class RentVsBuyResult(BaseModel):
    item_id: int
    item_name: str
    days: int
    rent_cost: float | None = None
    rent_available: bool = False
    buy_price: float | None = None
    buy_resale_loss: float | None = None
    recommendation: str = "insufficient_data"
    explanation: str = ""
    rental_platform: str | None = None
    buy_platform: str | None = None
    budget: float = 0
    buy_affordable: bool = False
    rent_affordable: bool | None = None
    deposit_required: bool = False
