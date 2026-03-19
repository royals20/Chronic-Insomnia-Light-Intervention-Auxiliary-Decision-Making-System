from datetime import datetime

from pydantic import BaseModel


class ImportErrorItem(BaseModel):
    row_number: int
    patient_code: str | None = None
    message: str


class ImportSummary(BaseModel):
    total_rows: int
    success_count: int
    failed_count: int
    created_count: int
    updated_count: int


class PatientImportResponse(BaseModel):
    message: str
    summary: ImportSummary
    errors: list[ImportErrorItem]


class ImportHistoryItem(BaseModel):
    id: int
    actor_name: str
    file_name: str | None = None
    action_type: str
    target_type: str
    target_id: str | None = None
    occurred_at: datetime
    detail_text: str | None = None
    total_rows: int | None = None
    success_count: int | None = None
    failed_count: int | None = None


class ImportHistoryResponse(BaseModel):
    items: list[ImportHistoryItem]
