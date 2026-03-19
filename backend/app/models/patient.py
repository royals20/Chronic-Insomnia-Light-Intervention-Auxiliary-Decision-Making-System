from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    anonymized_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gender: Mapped[str | None] = mapped_column(String(16), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    education_level: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    baseline_feature = relationship(
        "BaselineFeature",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    questionnaire_score = relationship(
        "QuestionnaireScore",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    sleep_metric = relationship(
        "SleepMetric",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    light_intervention = relationship(
        "LightIntervention",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    followup_outcome = relationship(
        "FollowupOutcome",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )
    prediction_result = relationship(
        "PredictionResult",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def has_baseline_feature(self) -> bool:
        return self.baseline_feature is not None

    @property
    def has_questionnaire_score(self) -> bool:
        return self.questionnaire_score is not None

    @property
    def has_sleep_metric(self) -> bool:
        return self.sleep_metric is not None

    @property
    def has_light_intervention(self) -> bool:
        return self.light_intervention is not None

    @property
    def has_followup_outcome(self) -> bool:
        return self.followup_outcome is not None
