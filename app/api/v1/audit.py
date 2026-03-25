from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.services.auditLogService import AuditLogService
from app.schemas.auditLogSchema import AuditLogOut, AuditLogListOut  # Import thêm ListOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee  # Nên chặn chỉ cho Admin/Nhân viên xem

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=APIResponse[AuditLogListOut])
def get_all_audit_logs(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
        log_type: Optional[str] = None,
        db: Session = Depends(get_db)
):
    service = AuditLogService(db)
    logs, total = service.get_all_logs(page=page, limit=limit, log_type=log_type)

    return APIResponse(
        status=True,
        code=200,
        message="Lấy danh sách lịch sử hệ thống thành công!",
        data=AuditLogListOut(logs=logs, total=total, page=page, limit=limit)
    )


@router.get("/{reference_id}", response_model=APIResponse[List[AuditLogOut]])
def get_audit_logs_by_reference(
        reference_id: UUID,
        db: Session = Depends(get_db)
):
    service = AuditLogService(db)
    logs = service.get_logs_for_entity(reference_id)
    return APIResponse(status=True, code=200, message="Thành công", data=logs)