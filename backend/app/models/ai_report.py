from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("items.id"))
    platform_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("platforms.id"))
    report_type: Mapped[str | None] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    report_text: Mapped[str | None] = mapped_column(Text)

    item: Mapped["Item"] = relationship("Item", back_populates="ai_reports")
    platform: Mapped["Platform"] = relationship("Platform", back_populates="ai_reports")
