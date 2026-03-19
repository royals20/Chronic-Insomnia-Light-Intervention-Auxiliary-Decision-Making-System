from datetime import datetime

from pydantic import BaseModel


class ReportPreviewSection(BaseModel):
    title: str
    content: list[str]


class ReportPreviewResponse(BaseModel):
    patient_id: int
    patient_code: str
    anonymized_code: str
    generated_at: datetime | None = None
    data_completeness_score: float | None = None
    benefit_score: float | None = None
    recommendation_level: str | None = None
    explanation_text: str | None = None
    key_factors: list[str]
    usage_limitations: list[str]
    footer_notice: str
    sections: list[ReportPreviewSection]
