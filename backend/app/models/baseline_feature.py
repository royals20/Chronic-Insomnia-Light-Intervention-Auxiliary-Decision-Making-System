from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BaselineFeature(Base):
    __tablename__ = "baseline_features"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    work_rest_schedule: Mapped[str | None] = mapped_column(String(128), nullable=True)
    disease_duration: Mapped[str | None] = mapped_column(String(128), nullable=True)
    medication_usage: Mapped[str | None] = mapped_column(Text, nullable=True)
    comorbidities: Mapped[str | None] = mapped_column(Text, nullable=True)
    psychological_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    sleep_habits: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="baseline_feature")
