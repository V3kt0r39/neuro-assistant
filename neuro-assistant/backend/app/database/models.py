from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DataOriginal(Base):
    __tablename__ = "data_original"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    concentration: Mapped[float] = mapped_column(Float, nullable=False)
    relaxation: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
