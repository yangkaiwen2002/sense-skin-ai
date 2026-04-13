from pydantic import BaseModel


class RentVsBuyRequest(BaseModel):
    days: int = 7
    budget: float = 500.0
    expected_resale_loss_pct: float = 0.04


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
