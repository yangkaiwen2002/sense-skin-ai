from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MarketEvent(Base):
    __tablename__ = "market_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str | None] = mapped_column(String)
    impact_scope: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    tags: Mapped[list["EventTag"]] = relationship("EventTag", back_populates="event")


class EventTag(Base):
    __tablename__ = "event_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("market_events.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String, nullable=False)

    event: Mapped["MarketEvent"] = relationship("MarketEvent", back_populates="tags")
