from pydantic import BaseModel
from typing import Literal
from uuid import UUID


class UserStatusUpdate(BaseModel):
    user_type: Literal["employee", "customer"]
    user_id: UUID
    status: str  # Should be one of HumanStatusEnum values


class PasswordResetRequest(BaseModel):
    user_type: Literal["employee", "customer"]
    user_id: UUID
    new_password: str
