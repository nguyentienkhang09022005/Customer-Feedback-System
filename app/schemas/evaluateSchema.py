from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class CustomerEvaluateOut(BaseModel):
    id_customer: UUID
    first_name: str
    last_name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class EvaluateCreate(BaseModel):
    id_ticket: UUID
    star: int = Field(..., ge=1, le=5, description="Số sao đánh giá phải từ 1 đến 5!")
    comment: Optional[str] = None


class EvaluateUpdate(BaseModel):
    star: Optional[int] = Field(None, ge=1, le=5, description="Số sao đánh giá phải từ 1 đến 5!")
    comment: Optional[str] = None


class EvaluateOut(BaseModel):
    id_evaluate: UUID
    id_ticket: UUID
    id_customer: UUID
    star: int
    comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    customer: Optional[CustomerEvaluateOut] = None

    class Config:
        from_attributes = True