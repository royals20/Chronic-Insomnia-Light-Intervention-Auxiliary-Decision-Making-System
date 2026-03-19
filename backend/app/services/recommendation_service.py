import json
from datetime import datetime
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models.model_version import ModelVersion
from app.models.patient import Patient
from app.models.prediction_result import PredictionResult
from app.schemas.recommendation import (
    BatchEvaluateResponse,
    RecommendationConfig,
    RecommendationEvaluationResult,
    RecommendationHistoryItem,
    RecommendationHistoryResponse,
)
from app.services.audit_service import add_audit_log
from app.services.patient_service import build_patient_detail_query
from app.services.recommendation_config_service import load_recommendation_config


RECOMMEND_LEVEL = "推荐光干预"
CAUTIOUS_LEVEL = "谨慎推荐并短期复评"
NOT_RECOMMEND_LEVEL = "暂不直接推荐"


def _get_nested_value(target: Any, path: str):
    current = target
    for part in path.split("."):
        if current is None:
            return None
        current = getattr(current, part, None)
    return current


def _has_value(value: Any) -> bool:
    return value not in (None, "", [], {})


def _normalize_number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _match_rule(value: Any, operator: str, expected: Any) -> bool:
    if value is None:
        return False

    if operator in {">", ">=", "<", "<="}:
        left = _normalize_number(value)
        right = _normalize_number(expected)
        if left is None or right is None:
            return False
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        return left <= right

    if operator == "==":
        return str(value) == str(expected)
    if operator == "!=":
        return str(value) != str(expected)
    if operator == "contains":
        return str(expected) in str(value)
    return False


def _calculate_data_completeness(patient: Patient, config: RecommendationConfig):
    total_weight = sum(field.weight for field in config.completeness_fields)
    completed_weight = 0.0
    missing_labels: list[str] = []
    for field in config.completeness_fields:
        value = _get_nested_value(patient, field.path)
        if _has_value(value):
            completed_weight += field.weight
        else:
            missing_labels.append(field.label)

    if total_weight <= 0:
        return 0.0, missing_labels
    return round(completed_weight / total_weight * 100, 2), missing_labels


def _calculate_benefit_score(patient: Patient, config: RecommendationConfig):
    benefit_score = config.base_benefit_score
    triggered_rules: list[dict[str, Any]] = []
    for rule in config.score_rules:
        value = _get_nested_value(patient, rule.field_path)
        if _match_rule(value, rule.operator, rule.value):
            benefit_score += rule.score_delta
            triggered_rules.append(
                {
                    "id": rule.id,
                    "label": rule.label,
                    "score_delta": rule.score_delta,
                    "factor_text": rule.factor_text,
                }
            )

    benefit_score = max(0.0, min(100.0, round(benefit_score, 2)))
    triggered_rules.sort(key=lambda item: abs(item["score_delta"]), reverse=True)
    return benefit_score, triggered_rules


def _build_recommendation_level(
    *,
    benefit_score: float,
    completeness_score: float,
    config: RecommendationConfig,
) -> str:
    thresholds = config.thresholds
    if completeness_score < thresholds.min_completeness_for_cautious:
        return NOT_RECOMMEND_LEVEL
    if (
        benefit_score >= thresholds.recommend_min_score
        and completeness_score >= thresholds.min_completeness_for_recommend
    ):
        return RECOMMEND_LEVEL
    if benefit_score >= thresholds.cautious_min_score:
        return CAUTIOUS_LEVEL
    return NOT_RECOMMEND_LEVEL


def _build_limitations(
    *,
    completeness_score: float,
    missing_labels: list[str],
    config: RecommendationConfig,
    patient: Patient,
) -> list[str]:
    limitations = list(config.limitation_templates)
    if missing_labels:
        limitations.append(
            "以下核心字段缺失，建议补录后再次评估：" + "、".join(missing_labels[:6])
        )
    if patient.light_intervention is None or not _has_value(patient.light_intervention.adherence):
        limitations.append("当前缺少依从性信息，相关执行可行性判断偏保守。")
    if completeness_score < config.thresholds.min_completeness_for_recommend:
        limitations.append("数据完整性未达到直接推荐阈值时，建议短期复评后再解释结果。")
    return limitations


def _build_explanation(
    *,
    completeness_score: float,
    benefit_score: float,
    recommendation_level: str,
    triggered_rules: list[dict[str, Any]],
) -> str:
    if triggered_rules:
        primary_factor = triggered_rules[0]["factor_text"]
    else:
        primary_factor = "当前已录入数据未触发明显的高权重获益或风险规则"
    return (
        f"数据完整性评分为 {completeness_score:.1f} 分，获益评分为 {benefit_score:.1f} 分。"
        f"当前推荐等级为“{recommendation_level}”。"
        f"关键解释：{primary_factor}。"
    )


def _ensure_rule_model_version(db: Session, config: RecommendationConfig) -> ModelVersion:
    model_version = db.scalar(
        select(ModelVersion).where(ModelVersion.name == config.model_version_name)
    )
    if model_version is None:
        model_version = ModelVersion(
            name=config.model_version_name,
            version_type="rule",
            status="active",
            description=f"{config.engine_name} {config.engine_version}",
        )
        db.add(model_version)
        db.flush()
    else:
        model_version.status = "active"
        model_version.description = f"{config.engine_name} {config.engine_version}"
    return model_version


def _serialize_rule_snapshot(config: RecommendationConfig) -> dict:
    return {
        "engine_name": config.engine_name,
        "engine_version": config.engine_version,
        "base_benefit_score": config.base_benefit_score,
        "thresholds": config.thresholds.model_dump(),
        "score_rule_count": len(config.score_rules),
        "completeness_field_count": len(config.completeness_fields),
    }


def _build_result_response(
    *,
    patient: Patient,
    generated_at: datetime,
    completeness_score: float,
    benefit_score: float,
    recommendation_level: str,
    explanation_text: str,
    key_factors: list[str],
    usage_limitations: list[str],
    config: RecommendationConfig,
    saved: bool,
) -> RecommendationEvaluationResult:
    return RecommendationEvaluationResult(
        patient_id=patient.id,
        patient_code=patient.patient_code,
        anonymized_code=patient.anonymized_code,
        generated_at=generated_at,
        data_completeness_score=completeness_score,
        benefit_score=benefit_score,
        recommendation_level=recommendation_level,
        explanation_text=explanation_text,
        key_factors=key_factors,
        usage_limitations=usage_limitations,
        engine_name=config.engine_name,
        engine_version=config.engine_version,
        saved=saved,
        model_version_name=config.model_version_name,
        rule_snapshot=_serialize_rule_snapshot(config),
    )


def evaluate_patient(
    db: Session,
    patient_id: int,
    *,
    save_result: bool = True,
) -> RecommendationEvaluationResult:
    config = load_recommendation_config()
    patient = db.scalar(build_patient_detail_query().where(Patient.id == patient_id))
    if patient is None:
        raise ValueError("患者不存在")

    completeness_score, missing_labels = _calculate_data_completeness(patient, config)
    benefit_score, triggered_rules = _calculate_benefit_score(patient, config)
    recommendation_level = _build_recommendation_level(
        benefit_score=benefit_score,
        completeness_score=completeness_score,
        config=config,
    )
    key_factors = [rule["factor_text"] for rule in triggered_rules[:5]]
    if not key_factors:
        key_factors = ["当前规则未触发高权重因子，建议结合更多随访与量表信息复核"]
    usage_limitations = _build_limitations(
        completeness_score=completeness_score,
        missing_labels=missing_labels,
        config=config,
        patient=patient,
    )
    explanation_text = _build_explanation(
        completeness_score=completeness_score,
        benefit_score=benefit_score,
        recommendation_level=recommendation_level,
        triggered_rules=triggered_rules,
    )
    generated_at = datetime.utcnow()
    saved = False

    if save_result:
        model_version = _ensure_rule_model_version(db, config)
        prediction = patient.prediction_result
        if prediction is None:
            prediction = PredictionResult(patient=patient)
            db.add(prediction)
        prediction.recommendation_level = recommendation_level
        prediction.score = benefit_score
        prediction.data_completeness_score = completeness_score
        prediction.explanation_text = explanation_text
        prediction.key_factors_text = json.dumps(key_factors, ensure_ascii=False)
        prediction.limitations_text = json.dumps(usage_limitations, ensure_ascii=False)
        prediction.engine_name = config.engine_name
        prediction.engine_version = config.engine_version
        prediction.rule_snapshot_text = json.dumps(
            _serialize_rule_snapshot(config),
            ensure_ascii=False,
        )
        prediction.generated_at = generated_at
        prediction.model_version = model_version
        add_audit_log(
            db,
            actor_name="research_demo",
            action_type="run_recommendation",
            target_type="prediction_result",
            target_id=str(patient.id),
            details={
                "patient_code": patient.patient_code,
                "recommendation_level": recommendation_level,
                "benefit_score": benefit_score,
                "data_completeness_score": completeness_score,
            },
            detail_text=f"生成患者 {patient.patient_code} 的推荐结果",
        )
        db.commit()
        saved = True

    return _build_result_response(
        patient=patient,
        generated_at=generated_at,
        completeness_score=completeness_score,
        benefit_score=benefit_score,
        recommendation_level=recommendation_level,
        explanation_text=explanation_text,
        key_factors=key_factors,
        usage_limitations=usage_limitations,
        config=config,
        saved=saved,
    )


def evaluate_patients_batch(
    db: Session,
    patient_ids: list[int],
    *,
    save_result: bool = True,
) -> BatchEvaluateResponse:
    results: list[RecommendationEvaluationResult] = []
    errors: list[str] = []
    for patient_id in patient_ids:
        try:
            results.append(evaluate_patient(db, patient_id, save_result=save_result))
        except ValueError as exc:
            errors.append(str(exc))

    return BatchEvaluateResponse(
        total_requested=len(patient_ids),
        success_count=len(results),
        failed_count=len(errors),
        results=results,
        errors=errors,
    )


def list_recommendation_history(
    db: Session,
    *,
    page: int,
    page_size: int,
    keyword: str | None = None,
    level: str | None = None,
) -> RecommendationHistoryResponse:
    stmt = (
        select(Patient, PredictionResult)
        .join(PredictionResult, PredictionResult.patient_id == Patient.id)
        .order_by(desc(PredictionResult.generated_at), desc(PredictionResult.updated_at))
    )
    count_stmt = select(func.count(PredictionResult.id)).join(
        Patient, PredictionResult.patient_id == Patient.id
    )

    filters = []
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Patient.patient_code.ilike(pattern),
                Patient.anonymized_code.ilike(pattern),
            )
        )
    if level:
        filters.append(PredictionResult.recommendation_level == level)

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0
    rows = db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = [
        RecommendationHistoryItem(
            patient_id=patient.id,
            patient_code=patient.patient_code,
            anonymized_code=patient.anonymized_code,
            recommendation_level=result.recommendation_level,
            benefit_score=result.benefit_score,
            data_completeness_score=result.data_completeness_score,
            engine_name=result.engine_name,
            engine_version=result.engine_version,
            generated_at=result.generated_at,
            updated_at=result.updated_at,
            explanation_text=result.explanation_text,
        )
        for patient, result in rows
    ]
    return RecommendationHistoryResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
