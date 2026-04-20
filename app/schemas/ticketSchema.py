from pydantic import BaseModel, computed_field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.paginationSchema import PaginationMeta


class TicketCreate(BaseModel):
    title: str
    severity: Optional[str] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None


class TicketAssign(BaseModel):
    id_employee: UUID


class TicketFromTemplateCreate(BaseModel):
    title: str
    severity: Optional[str] = None
    id_template: UUID
    custom_fields: Optional[dict] = None


class TicketOut(BaseModel):
    id_ticket: UUID
    title: str
    custom_fields: Optional[dict] = None
    status: str
    severity: Optional[str]
    expired_date: Optional[datetime] = None
    id_employee: Optional[UUID]
    id_customer: UUID
    id_template: Optional[UUID] = None
    template_version: Optional[int] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    template_name: Optional[str] = None

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
    template_name: Optional[str] = None
    template_fields_config: Optional[dict] = None

    class Config:
        from_attributes = True


class TicketResolve(BaseModel):
    resolution_note: Optional[str] = None


class TicketClose(BaseModel):
    reason: Optional[str] = None


class TicketReopen(BaseModel):
    reason: str


class TicketCustomerUpdate(BaseModel):
    title: Optional[str] = None
    custom_fields: Optional[dict] = None


class TicketListOut(BaseModel):
    items: List[TicketOut]
    meta: PaginationMeta
