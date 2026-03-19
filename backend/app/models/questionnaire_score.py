from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuestionnaireScore(Base):
    __tablename__ = "questionnaire_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    psqi_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    isi_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    anxiety_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    depression_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    assessed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="questionnaire_score")
