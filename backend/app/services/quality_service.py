from collections import Counter

from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.quality import AnomalyItem, ChartSeriesItem, CompletionStat, DataQualitySummary, MissingFieldStat
from app.services.patient_service import build_patient_detail_query


def _bool_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator * 100, 2)


def build_data_quality_summary(db: Session) -> DataQualitySummary:
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

    missing_fields = []
    completion_stats = []
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

    anomalies: list[AnomalyItem] = []
    for patient in patients:
        if patient.age is not None and (patient.age < 25 or patient.age > 55):
            anomalies.append(
                AnomalyItem(
                    patient_code=patient.patient_code,
                    anonymized_code=patient.anonymized_code,
                    issue_type="年龄需复核",
                    severity="medium",
                    message=f"年龄为 {patient.age} 岁，超出当前科研样本常见区间（25-55 岁）",
                )
            )

        if patient.sleep_metric is not None:
            metric = patient.sleep_metric
            if metric.sleep_efficiency is not None and (metric.sleep_efficiency < 65 or metric.sleep_efficiency > 95):
                anomalies.append(
                    AnomalyItem(
                        patient_code=patient.patient_code,
                        anonymized_code=patient.anonymized_code,
                        issue_type="睡眠效率需复核",
                        severity="high",
                        message=f"睡眠效率为 {metric.sleep_efficiency}%，建议复核数据来源或计算逻辑",
                    )
                )
            if metric.total_sleep_time_hours is not None and (metric.total_sleep_time_hours < 4.5 or metric.total_sleep_time_hours > 9):
                anomalies.append(
                    AnomalyItem(
                        patient_code=patient.patient_code,
                        anonymized_code=patient.anonymized_code,
                        issue_type="总睡眠时间需复核",
                        severity="medium",
                        message=f"总睡眠时间为 {metric.total_sleep_time_hours} 小时，建议结合原始记录复核",
                    )
                )

        if patient.light_intervention is not None:
            intervention = patient.light_intervention
            if intervention.intensity_lux is not None and intervention.intensity_lux > 4000:
                anomalies.append(
                    AnomalyItem(
                        patient_code=patient.patient_code,
                        anonymized_code=patient.anonymized_code,
                        issue_type="光照强度偏高",
                        severity="medium",
                        message=f"光照强度为 {intervention.intensity_lux} lux，建议核对干预方案记录",
                    )
                )
            if intervention.duration_minutes is not None and intervention.duration_minutes > 45:
                anomalies.append(
                    AnomalyItem(
                        patient_code=patient.patient_code,
                        anonymized_code=patient.anonymized_code,
                        issue_type="干预时长偏长",
                        severity="low",
                        message=f"持续时间为 {intervention.duration_minutes} 分钟，建议确认方案执行一致性",
                    )
                )

    gender_counter = Counter(patient.gender or "未填写" for patient in patients)
    gender_distribution = [
        ChartSeriesItem(name=name, value=value)
        for name, value in gender_counter.items()
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

    return DataQualitySummary(
        total_patients=total,
        missing_fields=missing_fields,
        completion_stats=completion_stats,
        anomalies=anomalies[:20],
        gender_distribution=gender_distribution,
        section_completion=section_completion,
        age_bucket_distribution=age_bucket_distribution,
    )
