from __future__ import annotations

import re
from collections import Counter

from sqlalchemy.orm import Session

from app.modeling.data_reader import build_causal_dataset
from app.models.patient import Patient
from app.schemas.quality import (
    ChartSeriesItem,
    CompletionStat,
    DataQualityOverviewSummary,
    DataQualityResponse,
    MissingFieldStat,
    QualityPatientIssue,
    QualitySuggestedFix,
)
from app.services.patient_service import build_patient_detail_query

DEFAULT_MODEL_MAX_FEATURES = 10
DEFAULT_MODEL_MIN_FEATURE_COVERAGE = 0.7


def _bool_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


def _first_number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    if match is None:
        return None
    return float(match.group())


def _average_completion_rate(completion_stats: list[CompletionStat]) -> float:
    if not completion_stats:
        return 0.0
    total = sum(item.completion_rate for item in completion_stats)
    return round(total / len(completion_stats), 2)


def _append_issue(
    issues: list[QualityPatientIssue],
    seen_keys: set[tuple[int | None, str]],
    *,
    patient: Patient | None,
    issue_code: str,
    issue_type: str,
    section: str,
    severity: str,
    message: str,
    suggested_action: str,
    blocking: bool,
) -> None:
    patient_id = patient.id if patient is not None else None
    issue_key = (patient_id, issue_code)
    if issue_key in seen_keys:
        return
    seen_keys.add(issue_key)
    issues.append(
        QualityPatientIssue(
            patient_id=patient_id,
            patient_code=patient.patient_code if patient is not None else None,
            anonymized_code=patient.anonymized_code if patient is not None else None,
            issue_code=issue_code,
            issue_type=issue_type,
            section=section,
            severity=severity,
            message=message,
            suggested_action=suggested_action,
            blocking=blocking,
        )
    )


def _patient_level_issues(patients: list[Patient]) -> list[QualityPatientIssue]:
    issues: list[QualityPatientIssue] = []
    seen_keys: set[tuple[int | None, str]] = set()

    for patient in patients:
        baseline = patient.baseline_feature
        questionnaire = patient.questionnaire_score
        sleep = patient.sleep_metric
        intervention = patient.light_intervention
        followup = patient.followup_outcome

        if baseline is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="missing_baseline_feature",
                issue_type="缺少基线特征",
                section="baseline",
                severity="high",
                message="当前缺少基线特征信息，无法完整描述干预前协变量。",
                suggested_action="补录病程、用药、心理状态等基线特征后再开展建模分析。",
                blocking=True,
            )
        if questionnaire is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="missing_questionnaire_score",
                issue_type="缺少量表评分",
                section="questionnaire",
                severity="high",
                message="当前缺少 PSQI/ISI 等量表信息，推荐与因果分析解释会明显受限。",
                suggested_action="补录量表评分及评估日期，保证基线症状信息完整。",
                blocking=True,
            )
        if sleep is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="missing_sleep_metric",
                issue_type="缺少睡眠指标",
                section="sleep",
                severity="high",
                message="当前缺少客观睡眠指标，模型无法充分表征睡眠状态。",
                suggested_action="补录总睡眠时间、入睡潜伏期、睡眠效率和觉醒次数。",
                blocking=True,
            )
        if intervention is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="missing_light_intervention",
                issue_type="缺少光干预记录",
                section="light",
                severity="high",
                message="当前缺少可比较的光干预记录，无法定义处理变量 T。",
                suggested_action="补录光照强度、持续时间、干预天数和依从性信息。",
                blocking=True,
            )
        if followup is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="missing_followup_outcome",
                issue_type="缺少随访结局",
                section="followup",
                severity="high",
                message="当前缺少随访结局，无法定义结局变量 Y。",
                suggested_action="补录主要或次要结局改善值，并记录随访日期。",
                blocking=True,
            )

        if patient.age is not None and (patient.age < 18 or patient.age > 80):
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="age_out_of_research_range",
                issue_type="年龄超出科研样本常见范围",
                section="patient",
                severity="medium",
                message=f"年龄为 {patient.age} 岁，建议确认是否属于当前研究纳入范围。",
                suggested_action="复核受试者纳排标准，必要时在分析时单独标记。",
                blocking=False,
            )

        if questionnaire is not None:
            if questionnaire.psqi_score is not None and not (0 <= questionnaire.psqi_score <= 21):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_psqi_score",
                    issue_type="PSQI 分值异常",
                    section="questionnaire",
                    severity="high",
                    message=f"PSQI 当前为 {questionnaire.psqi_score}，超出 0-21 的常见合法范围。",
                    suggested_action="核对量表原始录入值与换算规则。",
                    blocking=True,
                )
            if questionnaire.isi_score is not None and not (0 <= questionnaire.isi_score <= 28):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_isi_score",
                    issue_type="ISI 分值异常",
                    section="questionnaire",
                    severity="high",
                    message=f"ISI 当前为 {questionnaire.isi_score}，超出 0-28 的常见合法范围。",
                    suggested_action="核对 ISI 原始分值并修正异常记录。",
                    blocking=True,
                )
            if questionnaire.anxiety_score is not None and not (0 <= questionnaire.anxiety_score <= 21):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_anxiety_score",
                    issue_type="焦虑评分异常",
                    section="questionnaire",
                    severity="medium",
                    message=f"焦虑评分当前为 {questionnaire.anxiety_score}，超出 0-21 的常见范围。",
                    suggested_action="确认焦虑量表版本及录入方式。",
                    blocking=True,
                )
            if questionnaire.depression_score is not None and not (0 <= questionnaire.depression_score <= 27):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_depression_score",
                    issue_type="抑郁评分异常",
                    section="questionnaire",
                    severity="medium",
                    message=f"抑郁评分当前为 {questionnaire.depression_score}，超出 0-27 的常见范围。",
                    suggested_action="确认抑郁量表版本及录入方式。",
                    blocking=True,
                )
            if questionnaire.assessed_at is None:
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="missing_questionnaire_assessed_at",
                    issue_type="量表评估日期缺失",
                    section="questionnaire",
                    severity="low",
                    message="量表评分已填写，但缺少评估日期，时间顺序解释会受影响。",
                    suggested_action="补录量表评估日期，确保基线时间点清晰。",
                    blocking=False,
                )

        if sleep is not None:
            if sleep.total_sleep_time_hours is not None and not (0 <= sleep.total_sleep_time_hours <= 24):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_total_sleep_time",
                    issue_type="总睡眠时间异常",
                    section="sleep",
                    severity="high",
                    message=f"总睡眠时间为 {sleep.total_sleep_time_hours} 小时，超出 0-24 的合法范围。",
                    suggested_action="核对原始睡眠记录，修正单位或录入值。",
                    blocking=True,
                )
            if sleep.sleep_latency_minutes is not None and not (0 <= sleep.sleep_latency_minutes <= 600):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_sleep_latency",
                    issue_type="入睡潜伏期异常",
                    section="sleep",
                    severity="high",
                    message=f"入睡潜伏期为 {sleep.sleep_latency_minutes} 分钟，超出 0-600 的合法范围。",
                    suggested_action="核对入睡潜伏期单位与数据来源。",
                    blocking=True,
                )
            if sleep.sleep_efficiency is not None and not (0 <= sleep.sleep_efficiency <= 100):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_sleep_efficiency",
                    issue_type="睡眠效率异常",
                    section="sleep",
                    severity="high",
                    message=f"睡眠效率为 {sleep.sleep_efficiency}%，超出 0-100 的合法范围。",
                    suggested_action="复核睡眠效率计算公式或原始录入值。",
                    blocking=True,
                )
            if sleep.awakening_count is not None and not (0 <= sleep.awakening_count <= 20):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_awakening_count",
                    issue_type="觉醒次数异常",
                    section="sleep",
                    severity="medium",
                    message=f"觉醒次数为 {sleep.awakening_count}，超出 0-20 的常见范围。",
                    suggested_action="核对睡眠监测结果并修正异常录入。",
                    blocking=True,
                )

        if intervention is not None:
            if intervention.intensity_lux is not None and not (0 < intervention.intensity_lux <= 10000):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_intervention_intensity",
                    issue_type="光照强度异常",
                    section="light",
                    severity="high",
                    message=f"光照强度为 {intervention.intensity_lux} lux，超出 0-10000 的合法范围。",
                    suggested_action="核对设备或方案记录中的光照强度单位。",
                    blocking=True,
                )
            elif intervention.intensity_lux is not None and intervention.intensity_lux > 4000:
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="review_intervention_intensity",
                    issue_type="光照强度偏高",
                    section="light",
                    severity="medium",
                    message=f"光照强度为 {intervention.intensity_lux} lux，建议确认是否符合研究方案。",
                    suggested_action="复核光照方案与设备输出是否一致。",
                    blocking=False,
                )
            if intervention.duration_minutes is not None and not (0 < intervention.duration_minutes <= 180):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_intervention_duration",
                    issue_type="干预时长异常",
                    section="light",
                    severity="high",
                    message=f"持续时间为 {intervention.duration_minutes} 分钟，超出 1-180 的常见范围。",
                    suggested_action="核对干预持续时间和单位。",
                    blocking=True,
                )
            if intervention.intervention_days is not None and not (0 < intervention.intervention_days <= 365):
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="invalid_intervention_days",
                    issue_type="干预天数异常",
                    section="light",
                    severity="high",
                    message=f"干预天数为 {intervention.intervention_days} 天，超出 1-365 的常见范围。",
                    suggested_action="核对干预天数记录并确认方案持续时间。",
                    blocking=True,
                )

        if followup is not None:
            has_parseable_outcome = (
                _first_number(followup.primary_outcome) is not None
                or _first_number(followup.secondary_outcome) is not None
            )
            if not has_parseable_outcome:
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="unparseable_followup_outcome",
                    issue_type="随访结局不可解析",
                    section="followup",
                    severity="high",
                    message="已填写随访结局，但主要/次要结局中没有可提取的数值改善值。",
                    suggested_action="将结局写成可解析的数值改善值，例如“ISI 改善 6 分”。",
                    blocking=True,
                )
            if intervention is None:
                _append_issue(
                    issues,
                    seen_keys,
                    patient=patient,
                    issue_code="followup_without_intervention",
                    issue_type="随访结局缺少对应处理记录",
                    section="followup",
                    severity="high",
                    message="存在随访结局，但缺少光干预记录，无法建立 T 与 Y 的因果顺序。",
                    suggested_action="补录对应的光干预记录或核对该随访记录是否应纳入分析。",
                    blocking=True,
                )

        if intervention is not None and followup is None:
            _append_issue(
                issues,
                seen_keys,
                patient=patient,
                issue_code="intervention_without_followup",
                issue_type="干预后缺少随访结局",
                section="followup",
                severity="medium",
                message="已记录光干预，但没有对应随访结局，当前无法评估获益。",
                suggested_action="补录至少一个可量化的随访结局指标。",
                blocking=False,
            )

    return issues


def _aggregate_suggested_fixes(issues: list[QualityPatientIssue]) -> list[QualitySuggestedFix]:
    grouped: dict[str, dict] = {}
    for item in issues:
        payload = grouped.setdefault(
            item.issue_code,
            {
                "title": item.issue_type,
                "description": item.suggested_action,
                "priority": item.severity if item.blocking else item.severity,
                "affected_patient_ids": set(),
                "blocking": item.blocking,
            },
        )
        if item.patient_id is not None:
            payload["affected_patient_ids"].add(item.patient_id)
        if item.blocking and not payload["blocking"]:
            payload["blocking"] = True
            payload["priority"] = item.severity

    items = [
        QualitySuggestedFix(
            issue_code=issue_code,
            title=payload["title"],
            description=payload["description"],
            priority="high" if payload["blocking"] else payload["priority"],
            patient_count=len(payload["affected_patient_ids"]),
            affected_patient_ids=sorted(payload["affected_patient_ids"]),
        )
        for issue_code, payload in grouped.items()
    ]
    items.sort(
        key=lambda item: (
            0 if item.priority == "high" else 1 if item.priority == "medium" else 2,
            -item.patient_count,
            item.title,
        )
    )
    return items


def build_data_quality_summary(db: Session) -> DataQualityResponse:
    patients = db.scalars(build_patient_detail_query().order_by(Patient.created_at.asc())).all()
    total = len(patients)

    field_extractors = [
        ("性别", lambda p: p.gender),
        ("年龄", lambda p: p.age),
        ("教育程度", lambda p: p.education_level),
        ("基线特征", lambda p: p.baseline_feature),
        ("量表评分", lambda p: p.questionnaire_score),
        ("客观睡眠指标", lambda p: p.sleep_metric),
        ("光干预记录", lambda p: p.light_intervention),
        ("随访结局", lambda p: p.followup_outcome),
    ]

    missing_fields: list[MissingFieldStat] = []
    completion_stats: list[CompletionStat] = []
    for label, extractor in field_extractors:
        completed = sum(1 for patient in patients if extractor(patient) not in (None, "", []))
        missing = total - completed
        missing_fields.append(
            MissingFieldStat(
                field_label=label,
                missing_count=missing,
                missing_rate=_bool_rate(missing, total),
            )
        )
        completion_stats.append(
            CompletionStat(
                field_label=label,
                completed_count=completed,
                completion_rate=_bool_rate(completed, total),
            )
        )

    gender_distribution = [
        ChartSeriesItem(name=name, value=value)
        for name, value in Counter(patient.gender or "未填写" for patient in patients).items()
    ]
    section_completion = [
        ChartSeriesItem(name="基线特征", value=sum(1 for patient in patients if patient.has_baseline_feature)),
        ChartSeriesItem(name="量表评分", value=sum(1 for patient in patients if patient.has_questionnaire_score)),
        ChartSeriesItem(name="睡眠指标", value=sum(1 for patient in patients if patient.has_sleep_metric)),
        ChartSeriesItem(name="光干预", value=sum(1 for patient in patients if patient.has_light_intervention)),
        ChartSeriesItem(name="随访结局", value=sum(1 for patient in patients if patient.has_followup_outcome)),
    ]

    age_bucket_counter: Counter[str] = Counter()
    for patient in patients:
        if patient.age is None:
            age_bucket_counter["未填写"] += 1
        elif patient.age < 30:
            age_bucket_counter["30岁以下"] += 1
        elif patient.age < 40:
            age_bucket_counter["30-39岁"] += 1
        elif patient.age < 50:
            age_bucket_counter["40-49岁"] += 1
        else:
            age_bucket_counter["50岁及以上"] += 1
    age_bucket_distribution = [
        ChartSeriesItem(name=name, value=value)
        for name, value in age_bucket_counter.items()
    ]

    all_issues = _patient_level_issues(patients)
    seen_keys = {(item.patient_id, item.issue_code) for item in all_issues}
    causal_dataset = build_causal_dataset(
        db,
        max_features=DEFAULT_MODEL_MAX_FEATURES,
        min_feature_coverage=DEFAULT_MODEL_MIN_FEATURE_COVERAGE,
    )
    treated_count = sum(1 for record in causal_dataset.records if record.treatment == 1)
    control_count = len(causal_dataset.records) - treated_count

    if len(causal_dataset.records) < 12:
        _append_issue(
            all_issues,
            seen_keys,
            patient=None,
            issue_code="insufficient_modeling_samples",
            issue_type="因果建模样本不足",
            section="modeling",
            severity="high",
            message=f"当前仅有 {len(causal_dataset.records)} 条可用于因果建模的记录，低于 12 条最低建议值。",
            suggested_action="先补录缺少处理变量或结局变量的样本，再重新训练因果模型。",
            blocking=True,
        )
    if treated_count == 0 or control_count == 0:
        _append_issue(
            all_issues,
            seen_keys,
            patient=None,
            issue_code="non_separable_treatment_groups",
            issue_type="处理组与对照组不可分",
            section="modeling",
            severity="high",
            message="当前可建模样本只落在单一处理组，无法开展处理效果比较。",
            suggested_action="补充另一处理组的样本，确保增强方案与标准方案均有记录。",
            blocking=True,
        )
    if len(causal_dataset.selected_features) < 4:
        _append_issue(
            all_issues,
            seen_keys,
            patient=None,
            issue_code="insufficient_selected_features",
            issue_type="可用协变量不足",
            section="modeling",
            severity="high",
            message=f"当前仅有 {len(causal_dataset.selected_features)} 个满足覆盖率与方差要求的协变量，低于 4 个建模建议值。",
            suggested_action="优先补录量表、睡眠与基线变量，提升协变量覆盖率后再训练。",
            blocking=True,
        )
    low_coverage_features = [
        item["feature_label"]
        for item in causal_dataset.feature_coverage
        if item["coverage_rate"] < DEFAULT_MODEL_MIN_FEATURE_COVERAGE * 100
    ]
    if low_coverage_features:
        _append_issue(
            all_issues,
            seen_keys,
            patient=None,
            issue_code="low_feature_coverage",
            issue_type="关键建模特征覆盖率不足",
            section="modeling",
            severity="medium",
            message="以下特征覆盖率不足 70%：" + "、".join(low_coverage_features[:6]),
            suggested_action="补录低覆盖率特征，减少均值填补对因果结果稳定性的影响。",
            blocking=False,
        )

    blocking_issues = sorted(
        [item for item in all_issues if item.blocking],
        key=lambda item: (item.patient_id is None, item.section, item.patient_code or ""),
    )
    warning_issues = sorted(
        [item for item in all_issues if not item.blocking],
        key=lambda item: (item.patient_id is None, item.section, item.patient_code or ""),
    )
    affected_patient_ids = sorted(
        {
            item.patient_id
            for item in all_issues
            if item.patient_id is not None
        }
    )
    suggested_fixes = _aggregate_suggested_fixes(all_issues)

    complete_patients = sum(
        1
        for patient in patients
        if all(
            (
                patient.gender,
                patient.age is not None,
                patient.education_level,
                patient.baseline_feature,
                patient.questionnaire_score,
                patient.sleep_metric,
                patient.light_intervention,
                patient.followup_outcome,
            )
        )
    )

    return DataQualityResponse(
        summary=DataQualityOverviewSummary(
            total_patients=total,
            complete_patients=complete_patients,
            modeling_ready_patients=len(causal_dataset.records),
            blocking_issue_count=len(blocking_issues),
            warning_issue_count=len(warning_issues),
            affected_patient_count=len(affected_patient_ids),
            average_completion_rate=_average_completion_rate(completion_stats),
            missing_fields=missing_fields,
            completion_stats=completion_stats,
            gender_distribution=gender_distribution,
            section_completion=section_completion,
            age_bucket_distribution=age_bucket_distribution,
        ),
        blocking_issues=blocking_issues,
        warning_issues=warning_issues,
        suggested_fixes=suggested_fixes,
        affected_patient_ids=affected_patient_ids,
    )
