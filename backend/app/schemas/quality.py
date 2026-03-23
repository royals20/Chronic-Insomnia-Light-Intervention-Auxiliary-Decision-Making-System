from pydantic import BaseModel


class MissingFieldStat(BaseModel):
    field_label: str
    missing_count: int
    missing_rate: float


class CompletionStat(BaseModel):
    field_label: str
    completed_count: int
    completion_rate: float


class ChartSeriesItem(BaseModel):
    name: str
    value: int


class QualityPatientIssue(BaseModel):
    patient_id: int | None = None
    patient_code: str | None = None
    anonymized_code: str | None = None
    issue_code: str
    issue_type: str
    section: str
    severity: str
    message: str
    suggested_action: str
    blocking: bool


class QualitySuggestedFix(BaseModel):
    issue_code: str
    title: str
    description: str
    priority: str
    patient_count: int
    affected_patient_ids: list[int]


class DataQualityOverviewSummary(BaseModel):
    total_patients: int
    complete_patients: int
    modeling_ready_patients: int
    blocking_issue_count: int
    warning_issue_count: int
    affected_patient_count: int
    average_completion_rate: float
    missing_fields: list[MissingFieldStat]
    completion_stats: list[CompletionStat]
    gender_distribution: list[ChartSeriesItem]
    section_completion: list[ChartSeriesItem]
    age_bucket_distribution: list[ChartSeriesItem]


class DataQualityResponse(BaseModel):
    summary: DataQualityOverviewSummary
    blocking_issues: list[QualityPatientIssue]
    warning_issues: list[QualityPatientIssue]
    suggested_fixes: list[QualitySuggestedFix]
    affected_patient_ids: list[int]
