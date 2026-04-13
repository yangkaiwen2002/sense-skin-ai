from pydantic import BaseModel
from datetime import datetime


class EventSchema(BaseModel):
    id: int
    event_date: str
    event_type: str
    title: str
    summary: str | None = None
    impact_scope: str | None = None
    region: str | None = None
    tags: list[str] = []

    model_config = {"from_attributes": True}


class AIReportResponse(BaseModel):
    item_id: int
    item_name: str
    report_text: str
    generated_at: str
    report_type: str = "market_summary"
