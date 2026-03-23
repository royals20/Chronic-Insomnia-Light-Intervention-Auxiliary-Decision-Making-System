from datetime import datetime

from pydantic import BaseModel, Field


class FeatureCoverageItem(BaseModel):
    feature_name: str
    feature_label: str
    available_count: int
    missing_count: int
    coverage_rate: float
    variance: float
    selected: bool


class ValueCountItem(BaseModel):
    name: str
    value: int


class OutcomeSummary(BaseModel):
    min_value: float
    max_value: float
    mean_value: float


class DatasetOverviewResponse(BaseModel):
    total_patients: int
    eligible_records: int
    dropped_records: int
    selected_feature_names: list[str]
    treatment_name: str
    control_name: str
    outcome_name: str
    treatment_distribution: list[ValueCountItem]
    outcome_summary: OutcomeSummary | None = None
    feature_coverage: list[FeatureCoverageItem]
    dropped_examples: list[str]
    assumptions: list[str]
    limitations: list[str]


class CausalTrainingRequest(BaseModel):
    model_name: str | None = None
    test_ratio: float = Field(default=0.2, gt=0, lt=0.5)
    random_seed: int = Field(default=20260319)
    max_features: int = Field(default=10, ge=4, le=16)
    min_feature_coverage: float = Field(default=0.7, ge=0.3, le=1.0)
    feature_names: list[str] | None = None
    activate_after_train: bool = True


class ModelVersionSummary(BaseModel):
    id: int
    name: str
    version_type: str
    status: str
    description: str | None = None
    artifact_path: str | None = None
    engine_backend: str | None = None
    estimator_message: str | None = None
    reproducibility_status: str | None = None
    metrics: dict
    config: dict
    feature_list: list[str]
    selected_feature_keys: list[str] = []
    random_seed: int | None = None
    test_ratio: float | None = None
    min_feature_coverage: float | None = None
    artifact_generated_at: datetime | None = None
    training_started_at: datetime | None = None
    training_completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ActiveModelResponse(BaseModel):
    active_model: ModelVersionSummary | None = None


class HistogramBucket(BaseModel):
    name: str
    value: int


class FeatureImportanceItem(BaseModel):
    feature_name: str
    feature_label: str
    importance: float


class SubgroupResultItem(BaseModel):
    feature_name: str
    feature_label: str
    subgroup_name: str
    sample_count: int
    average_ite: float


class PatientEffectItem(BaseModel):
    patient_id: int
    patient_code: str
    anonymized_code: str
    treatment_label: str
    observed_outcome: float
    estimated_ite: float


class CausalEvaluationResultResponse(BaseModel):
    model_version: ModelVersionSummary
    ate: float
    validation_ate: float | None = None
    observed_group_difference: float | None = None
    engine_backend: str
    estimator_message: str
    reproducibility_status: str
    dataset_record_count: int
    train_record_count: int
    validation_record_count: int
    treatment_name: str
    control_name: str
    outcome_name: str
    selected_feature_names: list[str]
    selected_feature_keys: list[str]
    random_seed: int | None = None
    test_ratio: float | None = None
    min_feature_coverage: float | None = None
    artifact_generated_at: datetime | None = None
    ite_distribution: list[HistogramBucket]
    feature_importance: list[FeatureImportanceItem]
    subgroup_results: list[SubgroupResultItem]
    top_positive_patients: list[PatientEffectItem]
    top_negative_patients: list[PatientEffectItem]
    assumptions: list[str]
    limitations: list[str]


class CausalTrainingResponse(BaseModel):
    message: str
    model_version: ModelVersionSummary
    result: CausalEvaluationResultResponse
