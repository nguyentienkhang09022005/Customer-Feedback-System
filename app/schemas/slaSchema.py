from pydantic import BaseModel
from typing import Optional
from uuid import UUID

from app.core.constants import SeverityEnum

class SLACreate(BaseModel):
    policy_name: str
    severity: SeverityEnum
    max_resolution_minutes: int
    is_active: bool = True

class SLAUpdate(BaseModel):
    policy_name: Optional[str] = None
    severity: Optional[SeverityEnum] = None
    max_resolution_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class SLAOut(BaseModel):
    id_policy: UUID
    policy_name: str
    severity: SeverityEnum
    max_resolution_minutes: int
    is_active: bool

    class Config:
        from_attributes = True