from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.db.session import SessionLocal, init_db
from app.models.model_version import ModelVersion
from app.models.patient import Patient
from app.schemas.patient import (
    BaselineFeatureBase,
    FollowupOutcomeBase,
    LightInterventionBase,
    PatientCreate,
    PatientUpdate,
    PredictionResultBase,
    QuestionnaireScoreBase,
    SleepMetricBase,
)
from app.services.audit_service import add_audit_log
from app.services.patient_service import create_patient, update_patient


def build_payload(index: int, rng: random.Random) -> PatientCreate:
    genders = ["男", "女"]
    educations = ["高中", "本科", "硕士", "博士"]
    schedules = ["22:30-06:30", "23:00-07:00", "23:30-07:30", "00:00-08:00"]
    medication_patterns = ["未用药", "偶尔用药", "规律用药"]
    psych_states = ["稳定", "轻度焦虑", "轻度抑郁", "焦虑抑郁并存"]
    habits = ["睡前阅读", "睡前使用手机", "午睡偏长", "周末晚睡"]
    adherence_levels = ["高", "中", "低"]
    recommendation_levels = ["高", "中", "低"]
    model_names = ["规则基线版", "预测模型试验版", "因果推断试验版"]
    model_types = {
        "规则基线版": "rule",
        "预测模型试验版": "predictive",
        "因果推断试验版": "causal",
    }

    age = rng.randint(22, 58)
    height_cm = round(rng.uniform(150, 182), 1)
    weight_kg = round(rng.uniform(45, 83), 1)
    psqi = round(rng.uniform(8, 19), 1)
    isi = round(rng.uniform(10, 24), 1)
    anxiety = round(rng.uniform(2, 15), 1)
    depression = round(rng.uniform(1, 14), 1)
    total_sleep = round(rng.uniform(4.2, 7.1), 1)
    latency = round(rng.uniform(18, 68), 1)
    efficiency = round(rng.uniform(62, 91), 1)
    awakening_count = rng.randint(1, 5)
    intensity = round(rng.uniform(1800, 4500), 1)
    duration = rng.choice([20, 30, 45, 60])
    days = rng.choice([7, 14, 21, 28])
    score = round(rng.uniform(0.45, 0.95), 2)
    assessed_at = date(2026, 3, 1) + timedelta(days=index % 18)
    followup_date = assessed_at + timedelta(days=14)
    generated_at = datetime(2026, 3, 19, 9, 0, 0) + timedelta(minutes=index)
    model_name = rng.choice(model_names)

    return PatientCreate(
        patient_code=f"SEED-{index:04d}",
        anonymized_code=f"ANON-{index:04d}",
        gender=rng.choice(genders),
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
        education_level=rng.choice(educations),
        remarks="系统生成的科研演示模拟数据",
        baseline_feature=BaselineFeatureBase(
            work_rest_schedule=rng.choice(schedules),
            disease_duration=f"{rng.randint(3, 48)}个月",
            medication_usage=rng.choice(medication_patterns),
            comorbidities=rng.choice(["无", "偏头痛", "慢性疲劳", "过敏性鼻炎"]),
            psychological_status=rng.choice(psych_states),
            sleep_habits=rng.choice(habits),
            notes="用于原型展示的基线特征",
        ),
        questionnaire_score=QuestionnaireScoreBase(
            psqi_score=psqi,
            isi_score=isi,
            anxiety_score=anxiety,
            depression_score=depression,
            assessed_at=assessed_at,
        ),
        sleep_metric=SleepMetricBase(
            total_sleep_time_hours=total_sleep,
            sleep_latency_minutes=latency,
            sleep_efficiency=efficiency,
            awakening_count=awakening_count,
            notes="模拟睡眠监测摘要",
        ),
        light_intervention=LightInterventionBase(
            intensity_lux=intensity,
            start_period=rng.choice(["06:30", "07:00", "07:30", "08:00"]),
            duration_minutes=duration,
            intervention_days=days,
            adherence=rng.choice(adherence_levels),
            adverse_events=rng.choice(["无", "轻度眩光", "短暂眼疲劳"]),
        ),
        followup_outcome=FollowupOutcomeBase(
            followup_date=followup_date,
            primary_outcome=f"ISI较基线下降 {rng.randint(2, 8)} 分",
            secondary_outcome=f"睡眠效率提升 {rng.randint(3, 15)}%",
            notes="模拟两周随访结局",
        ),
        prediction_result=PredictionResultBase(
            recommendation_level=rng.choice(recommendation_levels),
            score=score,
            explanation_text="系统根据基线、量表与睡眠指标给出科研演示推荐结果",
            model_version_name=model_name,
            model_version_type=model_types[model_name],
            model_version_status="active",
            model_version_description="科研演示用模型版本",
            generated_at=generated_at,
        ),
    )


def seed_demo_data(total: int = 100) -> None:
    init_db()
    rng = random.Random(20260319)

    with SessionLocal() as db:
        for index in range(1, total + 1):
            payload = build_payload(index, rng)
            existing = db.scalar(select(Patient).where(Patient.patient_code == payload.patient_code))
            if existing is None:
                create_patient(db, payload)
            else:
                update_patient(
                    db,
                    existing,
                    PatientUpdate(
                        anonymized_code=payload.anonymized_code,
                        gender=payload.gender,
                        age=payload.age,
                        height_cm=payload.height_cm,
                        weight_kg=payload.weight_kg,
                        education_level=payload.education_level,
                        remarks=payload.remarks,
                        baseline_feature=payload.baseline_feature,
                        questionnaire_score=payload.questionnaire_score,
                        sleep_metric=payload.sleep_metric,
                        light_intervention=payload.light_intervention,
                        followup_outcome=payload.followup_outcome,
                        prediction_result=payload.prediction_result,
                    ),
                )

        model_count = db.query(ModelVersion).count()
        patient_count = db.query(Patient).count()
        add_audit_log(
            db,
            actor_name="system_seed",
            action_type="seed_demo_data",
            target_type="patients",
            detail_text=f"写入 {total} 例模拟患者数据",
            details={
                "seed_count": total,
                "patient_count": patient_count,
                "model_version_count": model_count,
            },
        )
        db.commit()

    print(f"模拟数据写入完成，共处理 {total} 例患者")


if __name__ == "__main__":
    seed_demo_data()
