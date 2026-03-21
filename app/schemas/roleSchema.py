from pydantic import BaseModel, Field
from typing import Optional

class RoleCreate(BaseModel):
    role_name: str = Field(..., max_length=50)
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    description: Optional[str] = None

class RoleOut(BaseModel):
    role_name: str
    description: Optional[str] = None
    class Config:
        from_attributes = True