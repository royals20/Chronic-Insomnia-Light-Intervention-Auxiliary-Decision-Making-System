from pydantic import BaseModel


class MissingFieldStat(BaseModel):
    field_label: str
    missing_count: int
    missing_rate: float


class CompletionStat(BaseModel):
    field_label: str
    completed_count: int
    completion_rate: float


class AnomalyItem(BaseModel):
    patient_code: str
    anonymized_code: str
    issue_type: str
    severity: str
    message: str


class ChartSeriesItem(BaseModel):
    name: str
    value: int


class DataQualitySummary(BaseModel):
    total_patients: int
    missing_fields: list[MissingFieldStat]
    completion_stats: list[CompletionStat]
    anomalies: list[AnomalyItem]
    gender_distribution: list[ChartSeriesItem]
    section_completion: list[ChartSeriesItem]
    age_bucket_distribution: list[ChartSeriesItem]
