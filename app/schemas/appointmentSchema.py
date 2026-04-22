from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class AppointmentCreate(BaseModel):
    id_ticket: UUID
    scheduled_at: datetime
    reason: str


class AppointmentOut(BaseModel):
    id_appointment: UUID
    id_ticket: UUID
    id_customer: UUID
    id_employee: UUID
    scheduled_at: datetime
    reason: str
    status: str
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AppointmentAccept(BaseModel):
    pass


class AppointmentReject(BaseModel):
    rejection_reason: str


class AppointmentCancel(BaseModel):
    pass


class AppointmentListOut(BaseModel):
    items: list[AppointmentOut]
    meta: dict