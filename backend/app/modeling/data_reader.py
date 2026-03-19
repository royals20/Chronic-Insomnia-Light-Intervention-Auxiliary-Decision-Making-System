from __future__ import annotations

import re
from statistics import mean

from sqlalchemy.orm import Session

from app.modeling.feature_selection import select_features
from app.modeling.types import CausalDataset, CausalRecord, FeatureSpec, RawCausalRow
from app.models.patient import Patient
from app.services.patient_service import build_patient_detail_query

TREATMENT_NAME = "增强光干预方案"
CONTROL_NAME = "标准光干预方案"
OUTCOME_NAME = "随访主要结局改善值"

_FEATURE_SPECS = [
    FeatureSpec("age", "年龄"),
    FeatureSpec("bmi", "体质指数"),
    FeatureSpec("gender_code", "性别编码"),
    FeatureSpec("education_level_code", "教育程度编码"),
    FeatureSpec("disease_duration_months", "病程（月）"),
    FeatureSpec("medication_level", "用药等级"),
    FeatureSpec("psychological_risk", "心理状态等级"),
    FeatureSpec("psqi_score", "PSQI"),
    FeatureSpec("isi_score", "ISI"),
    FeatureSpec("anxiety_score", "焦虑评分"),
    FeatureSpec("depression_score", "抑郁评分"),
    FeatureSpec("total_sleep_time_hours", "总睡眠时间"),
    FeatureSpec("sleep_latency_minutes", "入睡潜伏期"),
    FeatureSpec("sleep_efficiency", "睡眠效率"),
    FeatureSpec("awakening_count", "觉醒次数"),
]


def _first_number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if match is None:
        return None
    return float(match.group())


def _parse_disease_duration(value: str | None) -> float | None:
    number = _first_number(value)
    if number is None:
        return None
    if value and "年" in value:
        return round(number * 12, 2)
    return round(number, 2)


def _encode_gender(value: str | None) -> float | None:
    mapping = {"女": 0.0, "男": 1.0}
    return mapping.get(value) if value is not None else None


def _encode_education(value: str | None) -> float | None:
    mapping = {"高中": 1.0, "本科": 2.0, "硕士": 3.0, "博士": 4.0}
    return mapping.get(value) if value is not None else None


def _encode_medication(value: str | None) -> float | None:
    if not value:
        return None
    if "未" in value:
        return 0.0
    if "偶尔" in value:
        return 1.0
    if "规律" in value or "长期" in value:
        return 2.0
    return 1.0


def _encode_psychological_status(value: str | None) -> float | None:
    if not value:
        return None
    if "并存" in value:
        return 2.0
    if "焦虑" in value or "抑郁" in value:
        return 1.0
    return 0.0


def _calc_bmi(height_cm: float | None, weight_kg: float | None) -> float | None:
    if not height_cm or not weight_kg:
        return None
    height_m = height_cm / 100
    if height_m <= 0:
        return None
    return round(weight_kg / (height_m**2), 4)


def _derive_treatment(patient: Patient) -> tuple[int | None, str | None]:
    light = patient.light_intervention
    if light is None:
        return None, None

    enhanced_signals = 0
    if light.intensity_lux is not None and light.intensity_lux >= 3000:
        enhanced_signals += 1
    if light.duration_minutes is not None and light.duration_minutes >= 45:
        enhanced_signals += 1
    if light.intervention_days is not None and light.intervention_days >= 14:
        enhanced_signals += 1

    treatment = 1 if enhanced_signals >= 2 else 0
    return treatment, TREATMENT_NAME if treatment == 1 else CONTROL_NAME


def _derive_outcome(patient: Patient) -> float | None:
    followup = patient.followup_outcome
    if followup is None:
        return None

    primary = _first_number(followup.primary_outcome)
    if primary is not None:
        return round(primary, 4)

    secondary = _first_number(followup.secondary_outcome)
    if secondary is not None:
        return round(secondary, 4)
    return None


def _build_raw_feature_map(patient: Patient) -> dict[str, float | None]:
    baseline = patient.baseline_feature
    questionnaire = patient.questionnaire_score
    sleep = patient.sleep_metric
    return {
        "age": float(patient.age) if patient.age is not None else None,
        "bmi": _calc_bmi(patient.height_cm, patient.weight_kg),
        "gender_code": _encode_gender(patient.gender),
        "education_level_code": _encode_education(patient.education_level),
        "disease_duration_months": _parse_disease_duration(
            baseline.disease_duration if baseline else None
        ),
        "medication_level": _encode_medication(
            baseline.medication_usage if baseline else None
        ),
        "psychological_risk": _encode_psychological_status(
            baseline.psychological_status if baseline else None
        ),
        "psqi_score": float(questionnaire.psqi_score) if questionnaire and questionnaire.psqi_score is not None else None,
        "isi_score": float(questionnaire.isi_score) if questionnaire and questionnaire.isi_score is not None else None,
        "anxiety_score": float(questionnaire.anxiety_score) if questionnaire and questionnaire.anxiety_score is not None else None,
        "depression_score": float(questionnaire.depression_score) if questionnaire and questionnaire.depression_score is not None else None,
        "total_sleep_time_hours": float(sleep.total_sleep_time_hours) if sleep and sleep.total_sleep_time_hours is not None else None,
        "sleep_latency_minutes": float(sleep.sleep_latency_minutes) if sleep and sleep.sleep_latency_minutes is not None else None,
        "sleep_efficiency": float(sleep.sleep_efficiency) if sleep and sleep.sleep_efficiency is not None else None,
        "awakening_count": float(sleep.awakening_count) if sleep and sleep.awakening_count is not None else None,
    }


def build_causal_dataset(
    db: Session,
    *,
    max_features: int = 10,
    min_feature_coverage: float = 0.7,
    feature_names: list[str] | None = None,
) -> CausalDataset:
    patients = db.scalars(build_patient_detail_query().order_by(Patient.id.asc())).all()
    raw_rows: list[RawCausalRow] = []
    dropped_records: list[dict] = []

    for patient in patients:
        treatment, treatment_label = _derive_treatment(patient)
        outcome = _derive_outcome(patient)
        if treatment is None:
            dropped_records.append(
                {
                    "patient_id": patient.id,
                    "patient_code": patient.patient_code,
                    "reason": "缺少可比较的处理变量 T。",
                }
            )
            continue
        if outcome is None:
            dropped_records.append(
                {
                    "patient_id": patient.id,
                    "patient_code": patient.patient_code,
                    "reason": "缺少可解析的结局变量 Y。",
                }
            )
            continue

        raw_rows.append(
            RawCausalRow(
                patient_id=patient.id,
                patient_code=patient.patient_code,
                anonymized_code=patient.anonymized_code,
                treatment=treatment,
                treatment_label=treatment_label or CONTROL_NAME,
                outcome=outcome,
                features=_build_raw_feature_map(patient),
            )
        )

    candidate_features = list(_FEATURE_SPECS)
    if feature_names:
        requested = {name.strip() for name in feature_names if name.strip()}
        candidate_features = [
            spec for spec in _FEATURE_SPECS if spec.name in requested
        ] or candidate_features

    selected_features, coverage_summary = select_features(
        raw_rows,
        candidate_features,
        max_features=max_features,
        min_feature_coverage=min_feature_coverage,
    )

    selected_names = [spec.name for spec in selected_features]
    means = {
        feature_name: mean(
            [
                float(row.features[feature_name])
                for row in raw_rows
                if row.features.get(feature_name) is not None
            ]
        )
        for feature_name in selected_names
    }

    records: list[CausalRecord] = []
    for row in raw_rows:
        if not selected_names:
            continue
        observed_feature_count = sum(
            1 for feature_name in selected_names if row.features.get(feature_name) is not None
        )
        features = {
            feature_name: float(row.features[feature_name])
            if row.features.get(feature_name) is not None
            else float(means[feature_name])
            for feature_name in selected_names
        }
        records.append(
            CausalRecord(
                patient_id=row.patient_id,
                patient_code=row.patient_code,
                anonymized_code=row.anonymized_code,
                treatment=row.treatment,
                treatment_label=row.treatment_label,
                outcome=row.outcome,
                features=features,
                observed_feature_count=observed_feature_count,
            )
        )

    assumptions = [
        "X 使用基线协变量与基线睡眠相关指标，不引入随访结局变量。",
        "T 默认定义为“增强光干预方案”对比“标准光干预方案”，用于演示可比较处理场景。",
        "Y 默认从随访主要结局文本中提取改善值；若主要结局缺失，则退回次要结局中的数值。",
        "结果成立依赖可交换性、重叠性和稳定单元处理值等因果前提。",
    ]
    limitations = [
        "当前为科研演示流程，结局数值解析依赖文本格式，不能替代正式建模清洗。",
        "若本地未安装真实因果估计依赖，将自动使用占位估计器，仅用于界面与流程演示。",
        "仅供科研分析，不替代临床诊断与治疗。",
    ]

    return CausalDataset(
        total_patients=len(patients),
        records=records,
        selected_features=selected_features,
        feature_coverage=coverage_summary,
        treatment_name=TREATMENT_NAME,
        control_name=CONTROL_NAME,
        outcome_name=OUTCOME_NAME,
        dropped_records=dropped_records,
        assumptions=assumptions,
        limitations=limitations,
    )
