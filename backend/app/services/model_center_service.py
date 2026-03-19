from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from statistics import mean

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modeling.data_reader import build_causal_dataset
from app.modeling.estimators import build_causal_estimator
from app.modeling.splitter import train_validation_split
from app.modeling.types import CausalDataset, CausalRecord, FeatureSpec
from app.models.model_version import ModelVersion
from app.schemas.model_center import (
    ActiveModelResponse,
    CausalEvaluationResultResponse,
    CausalTrainingRequest,
    CausalTrainingResponse,
    DatasetOverviewResponse,
    FeatureCoverageItem,
    FeatureImportanceItem,
    HistogramBucket,
    ModelVersionSummary,
    OutcomeSummary,
    PatientEffectItem,
    SubgroupResultItem,
    ValueCountItem,
)
from app.services.audit_service import add_audit_log

settings = get_settings()
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff_-]+", "-", value).strip("-")
    return slug or "causal-model"


def _build_model_version_summary(model_version: ModelVersion) -> ModelVersionSummary:
    metrics = model_version.metrics
    config = model_version.config
    return ModelVersionSummary(
        id=model_version.id,
        name=model_version.name,
        version_type=model_version.version_type,
        status=model_version.status,
        description=model_version.description,
        artifact_path=model_version.artifact_path,
        engine_backend=metrics.get("engine_backend") or config.get("engine_backend"),
        metrics=metrics,
        config=config,
        feature_list=model_version.feature_list,
        training_started_at=model_version.training_started_at,
        training_completed_at=model_version.training_completed_at,
        created_at=model_version.created_at,
        updated_at=model_version.updated_at,
    )


def _ensure_unique_model_name(db: Session, name: str) -> str:
    candidate = name.strip() or f"因果获益演示模型-{datetime.now():%Y%m%d%H%M%S}"
    index = 1
    while db.scalar(select(ModelVersion).where(ModelVersion.name == candidate)) is not None:
        index += 1
        candidate = f"{name}-{index}"
    return candidate


def _build_histogram(values: list[float], bucket_count: int = 6) -> list[HistogramBucket]:
    if not values:
        return []

    min_value = min(values)
    max_value = max(values)
    if min_value == max_value:
        return [HistogramBucket(name=f"{min_value:.2f}", value=len(values))]

    width = (max_value - min_value) / bucket_count
    buckets = [0 for _ in range(bucket_count)]
    labels: list[str] = []
    for index in range(bucket_count):
        left = min_value + width * index
        right = min_value + width * (index + 1)
        labels.append(f"{left:.2f}~{right:.2f}")

    for value in values:
        index = min(int((value - min_value) / width), bucket_count - 1)
        buckets[index] += 1

    return [
        HistogramBucket(name=labels[index], value=buckets[index])
        for index in range(bucket_count)
    ]


def _pearson_abs(x_values: list[float], y_values: list[float]) -> float:
    if len(x_values) <= 1 or len(y_values) <= 1:
        return 0.0
    x_mean = mean(x_values)
    y_mean = mean(y_values)
    numerator = sum(
        (x_value - x_mean) * (y_value - y_mean)
        for x_value, y_value in zip(x_values, y_values, strict=False)
    )
    x_denom = sum((x_value - x_mean) ** 2 for x_value in x_values) ** 0.5
    y_denom = sum((y_value - y_mean) ** 2 for y_value in y_values) ** 0.5
    if x_denom == 0 or y_denom == 0:
        return 0.0
    return round(abs(numerator / (x_denom * y_denom)), 4)


def _feature_importance(
    dataset: CausalDataset,
    effects: list[float],
) -> list[FeatureImportanceItem]:
    items: list[FeatureImportanceItem] = []
    for spec in dataset.selected_features:
        feature_values = [record.features[spec.name] for record in dataset.records]
        items.append(
            FeatureImportanceItem(
                feature_name=spec.name,
                feature_label=spec.label,
                importance=_pearson_abs(feature_values, effects),
            )
        )
    return sorted(items, key=lambda item: item.importance, reverse=True)


def _subgroup_results(
    dataset: CausalDataset,
    effects: list[float],
    ranked_features: list[FeatureImportanceItem],
) -> list[SubgroupResultItem]:
    effect_by_patient = {
        record.patient_id: effect
        for record, effect in zip(dataset.records, effects, strict=False)
    }
    specs_by_name = {spec.name: spec for spec in dataset.selected_features}
    results: list[SubgroupResultItem] = []
    for item in ranked_features[:4]:
        spec = specs_by_name[item.feature_name]
        values = [record.features[spec.name] for record in dataset.records]
        if not values:
            continue
        ordered = sorted(values)
        median = ordered[len(ordered) // 2]
        low_group = [
            record for record in dataset.records if record.features[spec.name] <= median
        ]
        high_group = [
            record for record in dataset.records if record.features[spec.name] > median
        ]
        for subgroup_name, group_records in (
            ("低于或等于中位数", low_group),
            ("高于中位数", high_group),
        ):
            if not group_records:
                continue
            subgroup_effects = [
                effect_by_patient[record.patient_id]
                for record in group_records
            ]
            results.append(
                SubgroupResultItem(
                    feature_name=spec.name,
                    feature_label=spec.label,
                    subgroup_name=subgroup_name,
                    sample_count=len(group_records),
                    average_ite=round(mean(subgroup_effects), 4),
                )
            )
    return results


def _patient_effect_preview(
    dataset: CausalDataset,
    effects: list[float],
    *,
    reverse: bool,
) -> list[PatientEffectItem]:
    rows = [
        PatientEffectItem(
            patient_id=record.patient_id,
            patient_code=record.patient_code,
            anonymized_code=record.anonymized_code,
            treatment_label=record.treatment_label,
            observed_outcome=round(record.outcome, 4),
            estimated_ite=round(effect, 4),
        )
        for record, effect in zip(dataset.records, effects, strict=False)
    ]
    rows.sort(key=lambda item: item.estimated_ite, reverse=reverse)
    return rows[:6]


def _observed_group_difference(records: list[CausalRecord]) -> float | None:
    treated = [record.outcome for record in records if record.treatment == 1]
    control = [record.outcome for record in records if record.treatment == 0]
    if not treated or not control:
        return None
    return round(mean(treated) - mean(control), 4)


def _resolve_artifact_path(model_version: ModelVersion) -> Path:
    if not model_version.artifact_path:
        raise ValueError("当前模型版本尚未生成因果评估产物。")
    path = Path(model_version.artifact_path)
    if path.is_absolute():
        return path
    return BACKEND_ROOT / path


def _load_artifact(model_version: ModelVersion) -> dict:
    path = _resolve_artifact_path(model_version)
    if not path.exists():
        raise ValueError("模型产物文件不存在，请重新训练因果模型。")
    return json.loads(path.read_text(encoding="utf-8"))


def _build_result_response(
    model_version: ModelVersion,
    artifact: dict,
) -> CausalEvaluationResultResponse:
    return CausalEvaluationResultResponse(
        model_version=_build_model_version_summary(model_version),
        ate=float(artifact.get("ate", 0)),
        validation_ate=artifact.get("validation_ate"),
        observed_group_difference=artifact.get("observed_group_difference"),
        engine_backend=str(artifact.get("engine_backend", "unknown")),
        estimator_message=str(artifact.get("estimator_message", "")),
        dataset_record_count=int(artifact.get("dataset_record_count", 0)),
        train_record_count=int(artifact.get("train_record_count", 0)),
        validation_record_count=int(artifact.get("validation_record_count", 0)),
        treatment_name=str(artifact.get("treatment_name", "")),
        control_name=str(artifact.get("control_name", "")),
        outcome_name=str(artifact.get("outcome_name", "")),
        selected_feature_names=[str(item) for item in artifact.get("selected_feature_names", [])],
        ite_distribution=[
            HistogramBucket.model_validate(item)
            for item in artifact.get("ite_distribution", [])
        ],
        feature_importance=[
            FeatureImportanceItem.model_validate(item)
            for item in artifact.get("feature_importance", [])
        ],
        subgroup_results=[
            SubgroupResultItem.model_validate(item)
            for item in artifact.get("subgroup_results", [])
        ],
        top_positive_patients=[
            PatientEffectItem.model_validate(item)
            for item in artifact.get("top_positive_patients", [])
        ],
        top_negative_patients=[
            PatientEffectItem.model_validate(item)
            for item in artifact.get("top_negative_patients", [])
        ],
        assumptions=[str(item) for item in artifact.get("assumptions", [])],
        limitations=[str(item) for item in artifact.get("limitations", [])],
    )


def get_dataset_overview(
    db: Session,
    *,
    max_features: int = 10,
    min_feature_coverage: float = 0.7,
    feature_names: list[str] | None = None,
) -> DatasetOverviewResponse:
    dataset = build_causal_dataset(
        db,
        max_features=max_features,
        min_feature_coverage=min_feature_coverage,
        feature_names=feature_names,
    )
    treated_count = sum(1 for record in dataset.records if record.treatment == 1)
    control_count = len(dataset.records) - treated_count
    outcomes = [record.outcome for record in dataset.records]
    outcome_summary = None
    if outcomes:
        outcome_summary = OutcomeSummary(
            min_value=round(min(outcomes), 4),
            max_value=round(max(outcomes), 4),
            mean_value=round(mean(outcomes), 4),
        )

    return DatasetOverviewResponse(
        total_patients=dataset.total_patients,
        eligible_records=len(dataset.records),
        dropped_records=len(dataset.dropped_records),
        selected_feature_names=[spec.label for spec in dataset.selected_features],
        treatment_name=dataset.treatment_name,
        control_name=dataset.control_name,
        outcome_name=dataset.outcome_name,
        treatment_distribution=[
            ValueCountItem(name=dataset.control_name, value=control_count),
            ValueCountItem(name=dataset.treatment_name, value=treated_count),
        ],
        outcome_summary=outcome_summary,
        feature_coverage=[
            FeatureCoverageItem.model_validate(item)
            for item in dataset.feature_coverage
        ],
        dropped_examples=[
            f'{item["patient_code"]}: {item["reason"]}'
            for item in dataset.dropped_records[:5]
        ],
        assumptions=dataset.assumptions,
        limitations=dataset.limitations,
    )


def list_model_versions(
    db: Session,
    *,
    version_type: str | None = None,
) -> list[ModelVersionSummary]:
    stmt = select(ModelVersion).order_by(desc(ModelVersion.updated_at), desc(ModelVersion.id))
    if version_type:
        stmt = stmt.where(ModelVersion.version_type == version_type)
    rows = db.scalars(stmt).all()
    return [_build_model_version_summary(row) for row in rows]


def get_active_model(
    db: Session,
    *,
    version_type: str = "causal",
) -> ActiveModelResponse:
    model_version = db.scalar(
        select(ModelVersion)
        .where(
            ModelVersion.version_type == version_type,
            ModelVersion.status == "active",
        )
        .order_by(desc(ModelVersion.updated_at), desc(ModelVersion.id))
    )
    if model_version is None:
        return ActiveModelResponse(active_model=None)
    return ActiveModelResponse(active_model=_build_model_version_summary(model_version))


def activate_model_version(db: Session, version_id: int) -> ModelVersionSummary:
    model_version = db.get(ModelVersion, version_id)
    if model_version is None:
        raise ValueError("模型版本不存在。")

    siblings = db.scalars(
        select(ModelVersion).where(ModelVersion.version_type == model_version.version_type)
    ).all()
    for sibling in siblings:
        sibling.status = "inactive"
    model_version.status = "active"

    add_audit_log(
        db,
        actor_name=settings.demo_username,
        action_type="activate_model_version",
        target_type="model_version",
        target_id=str(model_version.id),
        details={
            "model_name": model_version.name,
            "version_type": model_version.version_type,
        },
        detail_text=f"激活模型版本 {model_version.name}",
    )
    db.commit()
    db.refresh(model_version)
    return _build_model_version_summary(model_version)


def train_causal_model(
    db: Session,
    payload: CausalTrainingRequest,
) -> CausalTrainingResponse:
    dataset = build_causal_dataset(
        db,
        max_features=payload.max_features,
        min_feature_coverage=payload.min_feature_coverage,
        feature_names=payload.feature_names,
    )
    if len(dataset.records) < 12:
        raise ValueError("可用于因果训练的记录不足，至少需要 12 条有效样本。")
    if len(dataset.selected_features) < 4:
        raise ValueError("可用于建模的协变量不足，请补充基线数据后重试。")

    train_records, validation_records = train_validation_split(
        dataset.records,
        test_ratio=payload.test_ratio,
        seed=payload.random_seed,
    )
    if len(train_records) < 8 or not validation_records:
        raise ValueError("训练/验证拆分失败，请调整测试集比例后重试。")

    requested_model_name = payload.model_name or f"因果获益演示模型-{datetime.now():%Y%m%d%H%M%S}"
    model_name = _ensure_unique_model_name(db, requested_model_name)
    started_at = datetime.utcnow()
    estimator = build_causal_estimator()
    estimator.fit(train_records, [spec.name for spec in dataset.selected_features])
    all_effects = estimator.effect(dataset.records)
    validation_effects = estimator.effect(validation_records)

    ranked_features = _feature_importance(dataset, all_effects)
    subgroup_results = _subgroup_results(dataset, all_effects, ranked_features)
    metrics = {
        "ate": round(mean(all_effects), 4),
        "validation_ate": round(mean(validation_effects), 4) if validation_effects else None,
        "observed_group_difference": _observed_group_difference(validation_records),
        "dataset_record_count": len(dataset.records),
        "train_record_count": len(train_records),
        "validation_record_count": len(validation_records),
        "engine_backend": estimator.backend_name,
    }
    completed_at = datetime.utcnow()

    if payload.activate_after_train:
        siblings = db.scalars(
            select(ModelVersion).where(ModelVersion.version_type == "causal")
        ).all()
        for sibling in siblings:
            sibling.status = "inactive"

    model_version = ModelVersion(
        name=model_name,
        version_type="causal",
        status="active" if payload.activate_after_train else "draft",
        description="演示级因果获益评估模型，默认比较增强光干预方案与标准光干预方案。",
        metrics_text=json.dumps(metrics, ensure_ascii=False),
        config_text=json.dumps(
            {
                "test_ratio": payload.test_ratio,
                "random_seed": payload.random_seed,
                "max_features": payload.max_features,
                "min_feature_coverage": payload.min_feature_coverage,
                "selected_feature_names": [spec.name for spec in dataset.selected_features],
                "engine_backend": estimator.backend_name,
            },
            ensure_ascii=False,
        ),
        feature_list_text=json.dumps(
            [spec.name for spec in dataset.selected_features],
            ensure_ascii=False,
        ),
        training_started_at=started_at,
        training_completed_at=completed_at,
    )
    db.add(model_version)
    db.flush()

    artifact_payload = {
        "ate": metrics["ate"],
        "validation_ate": metrics["validation_ate"],
        "observed_group_difference": metrics["observed_group_difference"],
        "engine_backend": estimator.backend_name,
        "estimator_message": (
            "当前结果基于可运行的因果估计接口生成。若本地已安装 econml/sklearn，将优先使用真实因果森林接口；"
            "否则自动回退到占位估计器。"
        ),
        "dataset_record_count": len(dataset.records),
        "train_record_count": len(train_records),
        "validation_record_count": len(validation_records),
        "treatment_name": dataset.treatment_name,
        "control_name": dataset.control_name,
        "outcome_name": dataset.outcome_name,
        "selected_feature_names": [spec.label for spec in dataset.selected_features],
        "selected_feature_keys": [spec.name for spec in dataset.selected_features],
        "ite_distribution": [bucket.model_dump() for bucket in _build_histogram(all_effects)],
        "feature_importance": [item.model_dump() for item in ranked_features[:10]],
        "subgroup_results": [item.model_dump() for item in subgroup_results],
        "top_positive_patients": [
            item.model_dump()
            for item in _patient_effect_preview(dataset, all_effects, reverse=True)
        ],
        "top_negative_patients": [
            item.model_dump()
            for item in _patient_effect_preview(dataset, all_effects, reverse=False)
        ],
        "assumptions": dataset.assumptions,
        "limitations": dataset.limitations,
    }

    artifact_file = settings.model_artifact_path / (
        f"causal_{model_version.id}_{_safe_slug(model_name)}.json"
    )
    artifact_file.write_text(
        json.dumps(artifact_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    model_version.artifact_path = str(artifact_file.relative_to(BACKEND_ROOT)).replace("\\", "/")

    add_audit_log(
        db,
        actor_name=settings.demo_username,
        action_type="train_causal_model",
        target_type="model_version",
        target_id=str(model_version.id),
        details={
            "model_name": model_version.name,
            "engine_backend": estimator.backend_name,
            "dataset_record_count": len(dataset.records),
            "ate": metrics["ate"],
        },
        detail_text=f"训练因果模型 {model_version.name}",
    )
    db.commit()
    db.refresh(model_version)

    result = _build_result_response(model_version, artifact_payload)
    return CausalTrainingResponse(
        message="因果获益评估模型训练完成，可用于演示级结果展示。",
        model_version=_build_model_version_summary(model_version),
        result=result,
    )


def get_causal_evaluation_result(
    db: Session,
    *,
    model_version_id: int | None = None,
) -> CausalEvaluationResultResponse:
    if model_version_id is None:
        model_version = db.scalar(
            select(ModelVersion)
            .where(
                ModelVersion.version_type == "causal",
                ModelVersion.status == "active",
                ModelVersion.artifact_path.is_not(None),
            )
            .order_by(desc(ModelVersion.updated_at), desc(ModelVersion.id))
        )
    else:
        model_version = db.get(ModelVersion, model_version_id)

    if model_version is None:
        raise ValueError("当前没有可展示的因果模型结果，请先在模型中心发起训练。")
    if model_version.version_type != "causal":
        raise ValueError("所选模型版本不是 causal 类型。")

    artifact = _load_artifact(model_version)
    return _build_result_response(model_version, artifact)
