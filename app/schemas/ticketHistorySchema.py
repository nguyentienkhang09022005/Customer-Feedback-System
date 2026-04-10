from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from uuid import UUID


class TicketHistoryOut(BaseModel):
    id_history: UUID
    id_ticket: UUID
    id_actor: Optional[UUID]
    actor_type: Optional[str]
    actor_name: Optional[str] = None
    action: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketHistoryListOut(BaseModel):
    items: list[TicketHistoryOut]
    total: int
