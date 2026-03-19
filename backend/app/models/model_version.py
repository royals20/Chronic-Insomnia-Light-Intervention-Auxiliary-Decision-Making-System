import json
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    version_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metrics_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature_list_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    training_completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    prediction_results = relationship("PredictionResult", back_populates="model_version")

    @property
    def metrics(self) -> dict:
        return self._parse_json_dict(self.metrics_text)

    @property
    def config(self) -> dict:
        return self._parse_json_dict(self.config_text)

    @property
    def feature_list(self) -> list[str]:
        if not self.feature_list_text:
            return []
        try:
            payload = json.loads(self.feature_list_text)
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [str(item) for item in payload]
        return []

    @staticmethod
    def _parse_json_dict(value: str | None) -> dict:
        if not value:
            return {}
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
