from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class NotificationCreate(BaseModel):
    title: str
    content: Optional[str] = None
    notification_type: Optional[str] = None
    id_reference: Optional[UUID] = None
    id_receiver: UUID

class NotificationOut(BaseModel):
    id_notification: UUID
    title: str
    content: Optional[str]
    notification_type: Optional[str]
    is_read: bool
    created_at: datetime
    id_reference: Optional[UUID]
    id_receiver: UUID

    class Config:
        from_attributes = True