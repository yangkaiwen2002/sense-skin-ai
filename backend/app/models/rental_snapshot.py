from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RentalSnapshot(Base):
    __tablename__ = "rental_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    daily_rental_price: Mapped[float | None] = mapped_column(Float)
    weekly_rental_price: Mapped[float | None] = mapped_column(Float)
    available_count: Mapped[int | None] = mapped_column(Integer)
    deposit_required: Mapped[bool] = mapped_column(Boolean, default=False)
    currency: Mapped[str] = mapped_column(String, default="CNY")

    item: Mapped["Item"] = relationship("Item", back_populates="rental_snapshots")
    platform: Mapped["Platform"] = relationship("Platform", back_populates="rental_snapshots")
