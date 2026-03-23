from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.recommendation import (
    BatchEvaluateRequest,
    BatchEvaluateResponse,
    RecommendationEvaluationResult,
    RecommendationHistoryResponse,
)
from app.schemas.user import UserRole
from app.services.recommendation_service import evaluate_patient, evaluate_patients_batch, list_recommendation_history

router = APIRouter(prefix="/recommendations", tags=["评估与推荐"])


@router.post("/evaluate/{patient_id}", response_model=RecommendationEvaluationResult, summary="单例评估")
def evaluate_single_patient(
    patient_id: int,
    save_result: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> RecommendationEvaluationResult:
    try:
        return evaluate_patient(
            db,
            patient_id,
            save_result=save_result,
            actor_name=current_user.username,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/evaluate-batch", response_model=BatchEvaluateResponse, summary="批量评估")
def evaluate_batch(
    payload: BatchEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> BatchEvaluateResponse:
    if not payload.patient_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请至少选择一例受试者")
    return evaluate_patients_batch(
        db,
        payload.patient_ids,
        save_result=payload.save_result,
        actor_name=current_user.username,
    )


@router.get("/history", response_model=RecommendationHistoryResponse, summary="推荐历史")
def get_recommendation_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    keyword: str | None = Query(default=None),
    level: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> RecommendationHistoryResponse:
    return list_recommendation_history(
        db,
        page=page,
        page_size=page_size,
        keyword=keyword,
        level=level,
    )
