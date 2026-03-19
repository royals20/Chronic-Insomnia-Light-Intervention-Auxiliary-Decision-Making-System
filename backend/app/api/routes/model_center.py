from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.model_center import (
    ActiveModelResponse,
    CausalEvaluationResultResponse,
    CausalTrainingRequest,
    CausalTrainingResponse,
    DatasetOverviewResponse,
    ModelVersionSummary,
)
from app.services.model_center_service import (
    activate_model_version,
    get_active_model,
    get_causal_evaluation_result,
    get_dataset_overview,
    list_model_versions,
    train_causal_model,
)

router = APIRouter(prefix="/model-center", tags=["模型中心"])


@router.get("/dataset-overview", response_model=DatasetOverviewResponse, summary="数据集概览")
def dataset_overview(
    max_features: int = Query(default=10, ge=4, le=16),
    min_feature_coverage: float = Query(default=0.7, ge=0.3, le=1.0),
    db: Session = Depends(get_db),
) -> DatasetOverviewResponse:
    return get_dataset_overview(
        db,
        max_features=max_features,
        min_feature_coverage=min_feature_coverage,
    )


@router.post("/train", response_model=CausalTrainingResponse, summary="发起因果训练")
def train_model(
    payload: CausalTrainingRequest,
    db: Session = Depends(get_db),
) -> CausalTrainingResponse:
    try:
        return train_causal_model(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/versions", response_model=list[ModelVersionSummary], summary="模型版本列表")
def version_list(
    version_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ModelVersionSummary]:
    return list_model_versions(db, version_type=version_type)


@router.get("/active-model", response_model=ActiveModelResponse, summary="当前激活模型")
def active_model(
    version_type: str = Query(default="causal"),
    db: Session = Depends(get_db),
) -> ActiveModelResponse:
    return get_active_model(db, version_type=version_type)


@router.post("/versions/{version_id}/activate", response_model=ModelVersionSummary, summary="激活模型版本")
def activate_version(
    version_id: int,
    db: Session = Depends(get_db),
) -> ModelVersionSummary:
    try:
        return activate_model_version(db, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/causal-results", response_model=CausalEvaluationResultResponse, summary="因果评估结果")
def causal_results(
    model_version_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> CausalEvaluationResultResponse:
    try:
        return get_causal_evaluation_result(db, model_version_id=model_version_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
