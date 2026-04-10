from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class CommentCreate(BaseModel):
    content: str
    is_internal: bool = False


class CommentUpdate(BaseModel):
    content: Optional[str] = None


class CommentOut(BaseModel):
    id_comment: UUID
    id_ticket: UUID
    id_author: UUID
    author_name: Optional[str] = None
    author_type: str
    content: str
    is_internal: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentListOut(BaseModel):
    items: list[CommentOut]
    total: int
