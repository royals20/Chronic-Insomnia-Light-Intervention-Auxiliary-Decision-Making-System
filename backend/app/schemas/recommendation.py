from datetime import datetime

from pydantic import BaseModel, Field


class RecommendationThresholds(BaseModel):
    recommend_min_score: float = Field(..., ge=0, le=100)
    cautious_min_score: float = Field(..., ge=0, le=100)
    min_completeness_for_recommend: float = Field(..., ge=0, le=100)
    min_completeness_for_cautious: float = Field(..., ge=0, le=100)


class CompletenessFieldConfig(BaseModel):
    label: str
    path: str
    weight: float = Field(..., ge=0)


class ScoreRuleConfig(BaseModel):
    id: str
    label: str
    field_path: str
    operator: str
    value: str | float | int
    score_delta: float
    factor_text: str


class RecommendationConfig(BaseModel):
    engine_name: str
    engine_version: str
    model_version_name: str
    base_benefit_score: float = Field(..., ge=0, le=100)
    thresholds: RecommendationThresholds
    completeness_fields: list[CompletenessFieldConfig]
    score_rules: list[ScoreRuleConfig]
    limitation_templates: list[str]
    report_footer_notice: str


class RecommendationEvaluationResult(BaseModel):
    patient_id: int
    patient_code: str
    anonymized_code: str
    generated_at: datetime
    data_completeness_score: float
    benefit_score: float
    recommendation_level: str
    explanation_text: str
    key_factors: list[str]
    usage_limitations: list[str]
    engine_name: str
    engine_version: str
    saved: bool
    model_version_name: str
    rule_snapshot: dict


class BatchEvaluateRequest(BaseModel):
    patient_ids: list[int]
    save_result: bool = True


class BatchEvaluateResponse(BaseModel):
    total_requested: int
    success_count: int
    failed_count: int
    results: list[RecommendationEvaluationResult]
    errors: list[str]


class RecommendationHistoryItem(BaseModel):
    patient_id: int
    patient_code: str
    anonymized_code: str
    recommendation_level: str | None = None
    benefit_score: float | None = None
    data_completeness_score: float | None = None
    engine_name: str | None = None
    engine_version: str | None = None
    generated_at: datetime | None = None
    updated_at: datetime
    explanation_text: str | None = None


class RecommendationHistoryResponse(BaseModel):
    items: list[RecommendationHistoryItem]
    total: int
    page: int
    page_size: int
