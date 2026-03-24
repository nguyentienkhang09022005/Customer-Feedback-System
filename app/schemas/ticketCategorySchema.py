from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TicketCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    department: str
    auto_assign: Optional[bool] = True

class TicketCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    department: Optional[str] = None
    auto_assign: Optional[bool] = None

class TicketCategoryOut(BaseModel):
    id_category: UUID
    name: str
    description: Optional[str]
    is_active: bool
    department: str
    auto_assign: bool
    created_at: datetime

    class Config:
        from_attributes = True