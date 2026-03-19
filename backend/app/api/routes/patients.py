from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.patient import Patient
from app.schemas.patient import (
    BaselineFeatureBase,
    FollowupOutcomeBase,
    LightInterventionBase,
    PatientCreate,
    PatientListResponse,
    PatientRead,
    PatientUpdate,
    QuestionnaireScoreBase,
    SleepMetricBase,
)
from app.services.patient_service import create_patient, delete_patient, get_patient_by_id, list_patients, update_patient

router = APIRouter(prefix="/patients", tags=["患者管理"])


@router.get("", response_model=PatientListResponse, summary="患者列表")
def get_patients(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None),
    gender: str | None = Query(default=None),
    has_baseline_feature: bool | None = Query(default=None),
    has_light_intervention: bool | None = Query(default=None),
    has_followup_outcome: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> PatientListResponse:
    total, items = list_patients(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        gender=gender,
        has_baseline_feature=has_baseline_feature,
        has_light_intervention=has_light_intervention,
        has_followup_outcome=has_followup_outcome,
    )
    return PatientListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{patient_id}", response_model=PatientRead, summary="患者详情")
def get_patient(patient_id: int, db: Session = Depends(get_db)) -> PatientRead:
    patient = get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return patient


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED, summary="创建患者")
def create_patient_endpoint(payload: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    existing = db.scalar(select(Patient).where(Patient.patient_code == payload.patient_code))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="患者编号已存在")
    return create_patient(db, payload)


@router.put("/{patient_id}", response_model=PatientRead, summary="更新患者")
def update_patient_endpoint(
    patient_id: int,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, payload)


@router.delete("/{patient_id}", summary="删除患者")
def delete_patient_endpoint(patient_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    delete_patient(db, patient)
    return {"message": "患者已删除"}


@router.put("/{patient_id}/baseline-feature", response_model=PatientRead, summary="保存基线特征")
def save_baseline_feature(
    patient_id: int,
    payload: BaselineFeatureBase,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, PatientUpdate(baseline_feature=payload))


@router.put("/{patient_id}/questionnaire-score", response_model=PatientRead, summary="保存量表评分")
def save_questionnaire_score(
    patient_id: int,
    payload: QuestionnaireScoreBase,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, PatientUpdate(questionnaire_score=payload))


@router.put("/{patient_id}/sleep-metric", response_model=PatientRead, summary="保存客观睡眠指标")
def save_sleep_metric(
    patient_id: int,
    payload: SleepMetricBase,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, PatientUpdate(sleep_metric=payload))


@router.put("/{patient_id}/light-intervention", response_model=PatientRead, summary="保存光干预记录")
def save_light_intervention(
    patient_id: int,
    payload: LightInterventionBase,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, PatientUpdate(light_intervention=payload))


@router.put("/{patient_id}/followup-outcome", response_model=PatientRead, summary="保存随访结局")
def save_followup_outcome(
    patient_id: int,
    payload: FollowupOutcomeBase,
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="患者不存在")
    return update_patient(db, patient, PatientUpdate(followup_outcome=payload))
