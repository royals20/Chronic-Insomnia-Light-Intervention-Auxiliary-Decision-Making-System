from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SleepMetric(Base):
    __tablename__ = "sleep_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_sleep_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_latency_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)
    awakening_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="sleep_metric")
