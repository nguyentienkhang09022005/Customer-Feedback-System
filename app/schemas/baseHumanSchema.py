from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class BaseHumanCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str = Field(..., pattern=r"^[0-9]{10,15}$")
    address: Optional[str] = None
    username: str
    password: str = Field(..., min_length=6)

class HumanOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    username: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True