from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.importing import ImportHistoryItem, ImportHistoryResponse, ImportSummary, PatientImportResponse
from app.schemas.user import UserRole
from app.services.import_service import generate_template_file, import_patients, load_rows_from_upload

router = APIRouter(prefix="/imports", tags=["数据导入"])


@router.get("/template", summary="下载受试者导入模板")
def download_template(
    format: str = Query(default="csv"),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.DATA_ENTRY)),
) -> Response:
    try:
        content, media_type, filename = generate_template_file(format)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


@router.post("/patients", response_model=PatientImportResponse, summary="导入受试者数据")
async def import_patients_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.DATA_ENTRY)),
) -> PatientImportResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未检测到上传文件")

    try:
        file_bytes = await file.read()
        rows = load_rows_from_upload(file.filename, file_bytes)
        result = import_patients(
            db,
            file_name=file.filename,
            rows=rows,
            actor_name=current_user.username,
        )
        return PatientImportResponse(
            message="导入完成" if result.failed_count == 0 else "导入完成，但存在部分失败记录",
            summary=ImportSummary(
                total_rows=result.total_rows,
                success_count=result.success_count,
                failed_count=result.failed_count,
                created_count=result.created_count,
                updated_count=result.updated_count,
            ),
            errors=result.errors,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/history", response_model=ImportHistoryResponse, summary="导入历史")
def get_import_history(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.DATA_ENTRY)),
) -> ImportHistoryResponse:
    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.action_type == "import_patients")
        .order_by(desc(AuditLog.occurred_at))
        .limit(limit)
    ).all()

    items = [
        ImportHistoryItem(
            id=log.id,
            actor_name=log.actor_name,
            file_name=(log.details or {}).get("file_name"),
            action_type=log.action_type,
            target_type=log.target_type,
            target_id=log.target_id,
            occurred_at=log.occurred_at,
            detail_text=log.detail_text,
            total_rows=(log.details or {}).get("total_rows"),
            success_count=(log.details or {}).get("success_count"),
            failed_count=(log.details or {}).get("failed_count"),
        )
        for log in logs
    ]
    return ImportHistoryResponse(items=items)
