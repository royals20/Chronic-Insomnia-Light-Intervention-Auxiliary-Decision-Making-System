import json

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.baseline_feature import BaselineFeature
from app.models.followup_outcome import FollowupOutcome
from app.models.light_intervention import LightIntervention
from app.models.model_version import ModelVersion
from app.models.patient import Patient
from app.models.prediction_result import PredictionResult
from app.models.questionnaire_score import QuestionnaireScore
from app.models.sleep_metric import SleepMetric
from app.schemas.patient import PatientCreate, PatientUpdate
from app.services.audit_service import add_audit_log

settings = get_settings()


def build_patient_detail_query():
    return (
        select(Patient)
        .options(
            selectinload(Patient.baseline_feature),
            selectinload(Patient.questionnaire_score),
            selectinload(Patient.sleep_metric),
            selectinload(Patient.light_intervention),
            selectinload(Patient.followup_outcome),
            selectinload(Patient.prediction_result).selectinload(PredictionResult.model_version),
        )
    )


def get_patient_by_id(db: Session, patient_id: int) -> Patient | None:
    return db.scalar(build_patient_detail_query().where(Patient.id == patient_id))


def list_patients(
    db: Session,
    *,
    page: int,
    page_size: int,
    keyword: str | None,
    gender: str | None = None,
    has_baseline_feature: bool | None = None,
    has_light_intervention: bool | None = None,
    has_followup_outcome: bool | None = None,
):
    filters = []
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Patient.patient_code.ilike(pattern),
                Patient.anonymized_code.ilike(pattern),
            )
        )
    if gender:
        filters.append(Patient.gender == gender)
    if has_baseline_feature is True:
        filters.append(Patient.baseline_feature.has())
    elif has_baseline_feature is False:
        filters.append(~Patient.baseline_feature.has())
    if has_light_intervention is True:
        filters.append(Patient.light_intervention.has())
    elif has_light_intervention is False:
        filters.append(~Patient.light_intervention.has())
    if has_followup_outcome is True:
        filters.append(Patient.followup_outcome.has())
    elif has_followup_outcome is False:
        filters.append(~Patient.followup_outcome.has())

    count_stmt = select(func.count(Patient.id))
    if filters:
        count_stmt = count_stmt.where(*filters)

    list_stmt = build_patient_detail_query().order_by(Patient.updated_at.desc())
    if filters:
        list_stmt = list_stmt.where(*filters)

    list_stmt = list_stmt.offset((page - 1) * page_size).limit(page_size)
    total = db.scalar(count_stmt) or 0
    items = db.scalars(list_stmt).all()
    return total, items


def _dump_section(section) -> dict:
    return section.model_dump(exclude_none=True) if section is not None else {}


def _sync_related_model(patient: Patient, relation_name: str, model_class, payload) -> None:
    data = _dump_section(payload)
    if not data:
        return

    existing = getattr(patient, relation_name)
    if existing is None:
        setattr(patient, relation_name, model_class(**data))
        return

    for key, value in data.items():
        setattr(existing, key, value)


def _resolve_model_version(db: Session, payload) -> ModelVersion | None:
    if payload is None or not payload.model_version_name:
        return None

    version = db.scalar(select(ModelVersion).where(ModelVersion.name == payload.model_version_name))
    if version is None:
        version = ModelVersion(
            name=payload.model_version_name,
            version_type=payload.model_version_type or "rule",
            status=payload.model_version_status or "active",
            description=payload.model_version_description,
        )
        db.add(version)
        db.flush()
    else:
        if payload.model_version_type:
            version.version_type = payload.model_version_type
        if payload.model_version_status:
            version.status = payload.model_version_status
        if payload.model_version_description:
            version.description = payload.model_version_description
    return version


def _sync_prediction_result(db: Session, patient: Patient, payload) -> None:
    data = _dump_section(payload)
    if not data:
        return

    version = _resolve_model_version(db, payload)
    prediction_data = {
        "recommendation_level": payload.recommendation_level,
        "score": payload.score,
        "data_completeness_score": payload.data_completeness_score,
        "explanation_text": payload.explanation_text,
        "key_factors_text": json.dumps(payload.key_factors, ensure_ascii=False) if payload.key_factors else None,
        "limitations_text": json.dumps(payload.usage_limitations, ensure_ascii=False) if payload.usage_limitations else None,
        "engine_name": payload.engine_name,
        "engine_version": payload.engine_version,
        "rule_snapshot_text": json.dumps(payload.rule_snapshot, ensure_ascii=False) if payload.rule_snapshot else None,
        "generated_at": payload.generated_at,
    }

    existing = patient.prediction_result
    if existing is None:
        patient.prediction_result = PredictionResult(
            **prediction_data,
            model_version=version,
        )
        return

    for key, value in prediction_data.items():
        setattr(existing, key, value)
    existing.model_version = version


def create_patient(db: Session, payload: PatientCreate) -> Patient:
    patient = Patient(
        **payload.model_dump(
            exclude={
                "baseline_feature",
                "questionnaire_score",
                "sleep_metric",
                "light_intervention",
                "followup_outcome",
                "prediction_result",
            }
        )
    )
    db.add(patient)
    db.flush()

    _sync_related_model(patient, "baseline_feature", BaselineFeature, payload.baseline_feature)
    _sync_related_model(patient, "questionnaire_score", QuestionnaireScore, payload.questionnaire_score)
    _sync_related_model(patient, "sleep_metric", SleepMetric, payload.sleep_metric)
    _sync_related_model(patient, "light_intervention", LightIntervention, payload.light_intervention)
    _sync_related_model(patient, "followup_outcome", FollowupOutcome, payload.followup_outcome)
    _sync_prediction_result(db, patient, payload.prediction_result)

    add_audit_log(
        db,
        actor_name=settings.demo_username,
        action_type="create_patient",
        target_type="patient",
        target_id=str(patient.id),
        details={"patient_code": patient.patient_code},
        detail_text=f"创建患者 {patient.patient_code}",
    )
    db.commit()
    return get_patient_by_id(db, patient.id)


def update_patient(db: Session, patient: Patient, payload: PatientUpdate) -> Patient:
    patient_data = payload.model_dump(
        exclude_none=True,
        exclude={
            "baseline_feature",
            "questionnaire_score",
            "sleep_metric",
            "light_intervention",
            "followup_outcome",
            "prediction_result",
        },
    )
    for key, value in patient_data.items():
        setattr(patient, key, value)

    _sync_related_model(patient, "baseline_feature", BaselineFeature, payload.baseline_feature)
    _sync_related_model(patient, "questionnaire_score", QuestionnaireScore, payload.questionnaire_score)
    _sync_related_model(patient, "sleep_metric", SleepMetric, payload.sleep_metric)
    _sync_related_model(patient, "light_intervention", LightIntervention, payload.light_intervention)
    _sync_related_model(patient, "followup_outcome", FollowupOutcome, payload.followup_outcome)
    _sync_prediction_result(db, patient, payload.prediction_result)

    add_audit_log(
        db,
        actor_name=settings.demo_username,
        action_type="update_patient",
        target_type="patient",
        target_id=str(patient.id),
        details={"patient_code": patient.patient_code},
        detail_text=f"更新患者 {patient.patient_code}",
    )
    db.commit()
    return get_patient_by_id(db, patient.id)


def delete_patient(db: Session, patient: Patient) -> None:
    patient_code = patient.patient_code
    patient_id = patient.id
    add_audit_log(
        db,
        actor_name=settings.demo_username,
        action_type="delete_patient",
        target_type="patient",
        target_id=str(patient_id),
        details={"patient_code": patient_code},
        detail_text=f"删除患者 {patient_code}",
    )
    db.delete(patient)
    db.commit()
