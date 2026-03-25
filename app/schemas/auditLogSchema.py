from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class AuditLogCreate(BaseModel):
    log_type: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    id_reference: UUID
    id_employee: UUID

class AuditLogOut(BaseModel):
    id_log: UUID
    log_type: str
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    id_reference: UUID
    id_employee: UUID

    class Config:
        from_attributes = True

class AuditLogListOut(BaseModel):
    logs: List[AuditLogOut]
    total: int
    page: int
    limit: int