import json
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    recommendation_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_factors_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    engine_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    engine_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rule_snapshot_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="prediction_result")
    model_version = relationship("ModelVersion", back_populates="prediction_results")

    @property
    def benefit_score(self) -> float | None:
        return self.score

    @property
    def key_factors(self) -> list[str]:
        return self._parse_json_list(self.key_factors_text)

    @property
    def usage_limitations(self) -> list[str]:
        return self._parse_json_list(self.limitations_text)

    @property
    def rule_snapshot(self) -> dict | None:
        if not self.rule_snapshot_text:
            return None
        try:
            payload = json.loads(self.rule_snapshot_text)
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_json_list(value: str | None) -> list[str]:
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except json.JSONDecodeError:
            return []
        return []
