from pydantic import BaseModel
from typing import Optional


class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#000000"
    description: Optional[str] = None


class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None


class TagOut(BaseModel):
    id_tag: str
    name: str
    color: str
    description: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
