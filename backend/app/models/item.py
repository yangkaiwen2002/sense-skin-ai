from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    weapon_type: Mapped[str | None] = mapped_column(String)
    skin_name: Mapped[str | None] = mapped_column(String)
    rarity: Mapped[str | None] = mapped_column(String)
    exterior: Mapped[str | None] = mapped_column(String)
    stattrak: Mapped[bool] = mapped_column(Boolean, default=False)
    souvenir: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[str | None] = mapped_column(String)
    icon_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    price_snapshots: Mapped[list] = relationship("PriceSnapshot", back_populates="item")
    rental_snapshots: Mapped[list] = relationship("RentalSnapshot", back_populates="item")
    ai_reports: Mapped[list] = relationship("AIReport", back_populates="item")
