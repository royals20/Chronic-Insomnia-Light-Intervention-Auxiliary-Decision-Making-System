from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.quality import DataQualityResponse
from app.schemas.user import UserRole
from app.services.quality_service import build_data_quality_summary

router = APIRouter(prefix="/quality", tags=["数据质量"])


@router.get("/summary", response_model=DataQualityResponse, summary="数据质量概览")
def get_quality_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER, UserRole.DATA_ENTRY)),
) -> DataQualityResponse:
    return build_data_quality_summary(db)
