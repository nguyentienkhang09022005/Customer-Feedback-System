from pydantic import BaseModel, Field
from typing import Optional

class CustomerTypeCreate(BaseModel):
    type_name: str = Field(..., max_length=50)
    description: Optional[str] = None

class CustomerTypeUpdate(BaseModel):
    description: Optional[str] = None

class CustomerTypeOut(BaseModel):
    type_name: str
    description: Optional[str] = None
    class Config:
        from_attributes = True