from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    platform_id: Mapped[int] = mapped_column(Integer, ForeignKey("platforms.id"), nullable=False)
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    listing_price: Mapped[float | None] = mapped_column(Float)
    buy_order_price: Mapped[float | None] = mapped_column(Float)
    avg_price_24h: Mapped[float | None] = mapped_column(Float)
    volume_24h: Mapped[int | None] = mapped_column(Integer)
    liquidity_depth: Mapped[int | None] = mapped_column(Integer)
    spread: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="CNY")

    item: Mapped["Item"] = relationship("Item", back_populates="price_snapshots")
    platform: Mapped["Platform"] = relationship("Platform", back_populates="price_snapshots")
