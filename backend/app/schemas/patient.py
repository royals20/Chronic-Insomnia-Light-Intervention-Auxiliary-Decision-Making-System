from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BaselineFeatureBase(BaseModel):
    work_rest_schedule: str | None = Field(default=None, description="作息")
    disease_duration: str | None = Field(default=None, description="病程")
    medication_usage: str | None = Field(default=None, description="用药")
    comorbidities: str | None = Field(default=None, description="合并症")
    psychological_status: str | None = Field(default=None, description="心理状态")
    sleep_habits: str | None = Field(default=None, description="睡眠习惯")
    notes: str | None = Field(default=None, description="备注")


class BaselineFeatureRead(BaselineFeatureBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionnaireScoreBase(BaseModel):
    psqi_score: float | None = None
    isi_score: float | None = None
    anxiety_score: float | None = None
    depression_score: float | None = None
    assessed_at: date | None = None


class QuestionnaireScoreRead(QuestionnaireScoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SleepMetricBase(BaseModel):
    total_sleep_time_hours: float | None = None
    sleep_latency_minutes: float | None = None
    sleep_efficiency: float | None = None
    awakening_count: int | None = None
    notes: str | None = None


class SleepMetricRead(SleepMetricBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LightInterventionBase(BaseModel):
    intensity_lux: float | None = None
    start_period: str | None = None
    duration_minutes: int | None = None
    intervention_days: int | None = None
    adherence: str | None = None
    adverse_events: str | None = None


class LightInterventionRead(LightInterventionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FollowupOutcomeBase(BaseModel):
    followup_date: date | None = None
    primary_outcome: str | None = None
    secondary_outcome: str | None = None
    notes: str | None = None


class FollowupOutcomeRead(FollowupOutcomeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ModelVersionRead(BaseModel):
    id: int
    name: str
    version_type: str
    status: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PredictionResultBase(BaseModel):
    data_completeness_score: float | None = None
    recommendation_level: str | None = None
    score: float | None = None
    explanation_text: str | None = None
    key_factors: list[str] | None = None
    usage_limitations: list[str] | None = None
    engine_name: str | None = None
    engine_version: str | None = None
    rule_snapshot: dict | None = None
    model_version_name: str | None = None
    model_version_type: str | None = None
    model_version_status: str | None = None
    model_version_description: str | None = None
    generated_at: datetime | None = None


class PredictionResultRead(BaseModel):
    id: int
    data_completeness_score: float | None = None
    benefit_score: float | None = None
    recommendation_level: str | None = None
    score: float | None = None
    explanation_text: str | None = None
    key_factors: list[str] = []
    usage_limitations: list[str] = []
    engine_name: str | None = None
    engine_version: str | None = None
    rule_snapshot: dict | None = None
    generated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    model_version: ModelVersionRead | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    patient_code: str = Field(..., min_length=1, max_length=64, description="患者编号")
    anonymized_code: str = Field(..., min_length=1, max_length=64, description="匿名编号")
    gender: str | None = Field(default=None, max_length=16)
    age: int | None = Field(default=None, ge=0, le=120)
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    education_level: str | None = Field(default=None, max_length=64)
    remarks: str | None = None


class PatientCreate(PatientBase):
    baseline_feature: BaselineFeatureBase | None = None
    questionnaire_score: QuestionnaireScoreBase | None = None
    sleep_metric: SleepMetricBase | None = None
    light_intervention: LightInterventionBase | None = None
    followup_outcome: FollowupOutcomeBase | None = None
    prediction_result: PredictionResultBase | None = None


class PatientUpdate(BaseModel):
    anonymized_code: str | None = Field(default=None, min_length=1, max_length=64)
    gender: str | None = Field(default=None, max_length=16)
    age: int | None = Field(default=None, ge=0, le=120)
    height_cm: float | None = Field(default=None, ge=0, le=300)
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    education_level: str | None = Field(default=None, max_length=64)
    remarks: str | None = None
    baseline_feature: BaselineFeatureBase | None = None
    questionnaire_score: QuestionnaireScoreBase | None = None
    sleep_metric: SleepMetricBase | None = None
    light_intervention: LightInterventionBase | None = None
    followup_outcome: FollowupOutcomeBase | None = None
    prediction_result: PredictionResultBase | None = None


class PatientListItem(PatientBase):
    id: int
    created_at: datetime
    updated_at: datetime
    has_baseline_feature: bool
    has_questionnaire_score: bool
    has_sleep_metric: bool
    has_light_intervention: bool
    has_followup_outcome: bool

    model_config = ConfigDict(from_attributes=True)


class PatientRead(PatientListItem):
    baseline_feature: BaselineFeatureRead | None = None
    questionnaire_score: QuestionnaireScoreRead | None = None
    sleep_metric: SleepMetricRead | None = None
    light_intervention: LightInterventionRead | None = None
    followup_outcome: FollowupOutcomeRead | None = None
    prediction_result: PredictionResultRead | None = None


class PatientListResponse(BaseModel):
    items: list[PatientListItem]
    total: int
    page: int
    page_size: int
