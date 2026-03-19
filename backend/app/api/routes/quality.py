from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.quality import DataQualitySummary
from app.services.quality_service import build_data_quality_summary

router = APIRouter(prefix="/quality", tags=["数据质量"])


@router.get("/summary", response_model=DataQualitySummary, summary="数据质量统计")
def get_quality_summary(db: Session = Depends(get_db)) -> DataQualitySummary:
    return build_data_quality_summary(db)
