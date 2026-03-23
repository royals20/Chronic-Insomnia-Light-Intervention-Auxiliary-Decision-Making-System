from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.user import User
from app.schemas.report import ReportPreviewResponse
from app.schemas.user import UserRole
from app.services.recommendation_service import list_recommendation_history
from app.services.report_service import build_report_preview, render_export_csv, render_report_html

router = APIRouter(prefix="/reports", tags=["报告中心"])


@router.get("/preview/{patient_id}", response_model=ReportPreviewResponse, summary="单例报告预览")
def get_report_preview(
    patient_id: int,
    auto_generate: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> ReportPreviewResponse:
    try:
        return build_report_preview(db, patient_id, auto_generate=auto_generate)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/html/{patient_id}", summary="打印友好的 HTML 报告")
def get_report_html(
    patient_id: int,
    auto_generate: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> Response:
    try:
        report = build_report_preview(db, patient_id, auto_generate=auto_generate)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(content=render_report_html(report), media_type="text/html; charset=utf-8")


@router.get("/export-list.csv", summary="批量导出清单")
def export_report_list(
    keyword: str | None = Query(default=None),
    level: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.RESEARCHER)),
) -> Response:
    history = list_recommendation_history(
        db,
        page=1,
        page_size=500,
        keyword=keyword,
        level=level,
    )
    rows = [
        build_report_preview(db, item.patient_id, auto_generate=False)
        for item in history.items
    ]
    headers = {
        "Content-Disposition": 'attachment; filename="recommendation_report_list.csv"'
    }
    return Response(
        content=render_export_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )
