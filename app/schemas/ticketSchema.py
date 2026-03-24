from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


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
    id_category: UUID
    id_employee: Optional[UUID]
    id_customer: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketDetailOut(TicketOut):
    assigned_employee: Optional[dict] = None

    class Config:
        from_attributes = True
