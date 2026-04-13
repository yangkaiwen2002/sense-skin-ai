from __future__ import annotations
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    supports_rental: Mapped[bool] = mapped_column(Boolean, default=False)
    region: Mapped[str | None] = mapped_column(String)
    notes: Mapped[str | None] = mapped_column(String)

    price_snapshots: Mapped[list] = relationship("PriceSnapshot", back_populates="platform")
    rental_snapshots: Mapped[list] = relationship("RentalSnapshot", back_populates="platform")
    ai_reports: Mapped[list] = relationship("AIReport", back_populates="platform")
