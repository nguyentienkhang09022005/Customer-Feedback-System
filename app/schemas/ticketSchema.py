from pydantic import BaseModel, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.paginationSchema import PaginationMeta


class TicketCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: Optional[str] = None
    id_category: UUID


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    id_category: Optional[UUID] = None


class TicketAssign(BaseModel):
    id_employee: UUID


class TicketOut(BaseModel):
    id_ticket: UUID
    title: str
    description: Optional[str]
    status: str
    severity: Optional[str]
    expired_date: Optional[datetime] = None
    id_category: UUID
    id_employee: Optional[UUID]
    id_customer: UUID
    created_at: datetime
    updated_at: datetime
    category_name: Optional[str] = None

    @computed_field
    @property
    def is_overdue(self) -> bool:
        if self.expired_date and self.status not in ["Resolved", "Closed"]:
            return datetime.utcnow() > self.expired_date
        return False

    class Config:
        from_attributes = True


class TicketDetailOut(TicketOut):
    assigned_employee: Optional[dict] = None

    class Config:
        from_attributes = True


class TicketResolve(BaseModel):
    resolution_note: Optional[str] = None


class TicketClose(BaseModel):
    reason: Optional[str] = None


class TicketReopen(BaseModel):
    reason: str  # Bắt buộc - lý do mở lại ticket


class TicketListOut(BaseModel):
    items: List[TicketOut]
    meta: PaginationMeta
