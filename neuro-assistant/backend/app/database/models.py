from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_calibration_user: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    eeg_records: Mapped[list["EEGRecord"]] = relationship(back_populates="user")


class EEGRecord(Base):
    __tablename__ = "eeg_records"
    __table_args__ = (
        CheckConstraint("concentration BETWEEN 0 AND 100", name="chk_eeg_records_concentration_range"),
        CheckConstraint("relaxation BETWEEN 0 AND 100", name="chk_eeg_records_relaxation_range"),
        CheckConstraint(
            "self_reported_emotion IN ('SAD', 'HAPPY', 'CALM')",
            name="chk_eeg_records_emotion_values",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    concentration: Mapped[float] = mapped_column(Float, nullable=False)
    relaxation: Mapped[float] = mapped_column(Float, nullable=False)
    self_reported_emotion: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="eeg_records")


class EmotionThreshold(Base):
    __tablename__ = "emotion_thresholds"
    __table_args__ = (
        CheckConstraint("emotion IN ('SAD', 'HAPPY', 'CALM')", name="chk_emotion_thresholds_emotion_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    emotion: Mapped[str] = mapped_column(String(10), nullable=False, unique=True, index=True)
    conc_avg: Mapped[float] = mapped_column(Float, nullable=False)
    relax_avg: Mapped[float] = mapped_column(Float, nullable=False)
    conc_min: Mapped[float] = mapped_column(Float, nullable=False)
    conc_max: Mapped[float] = mapped_column(Float, nullable=False)
    relax_min: Mapped[float] = mapped_column(Float, nullable=False)
    relax_max: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        CheckConstraint("detected_emotion IN ('SAD', 'HAPPY', 'CALM')", name="chk_user_sessions_emotion_values"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    detected_emotion: Mapped[str] = mapped_column(String(10), nullable=False)
    concentration: Mapped[float] = mapped_column(Float, nullable=False)
    relaxation: Mapped[float] = mapped_column(Float, nullable=False)
    ai_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())