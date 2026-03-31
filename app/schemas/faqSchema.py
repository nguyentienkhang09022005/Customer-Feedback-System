from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.paginationSchema import PaginationMeta

class FAQCreate(BaseModel):
    title: str
    content: str
    is_published: bool = True
    id_category: UUID

class FAQUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None
    id_category: Optional[UUID] = None

class FAQAuthorOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    class Config:
        from_attributes = True

class FAQCategoryOut(BaseModel):
    id_category: Optional[UUID] = None
    name: Optional[str] = None
    class Config:
        from_attributes = True

class FAQListOut(BaseModel):
    id_article: UUID
    title: str
    view_count: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
    id_category: Optional[UUID] = None
    id_author: UUID
    author: Optional[FAQAuthorOut] = None
    category: Optional[FAQCategoryOut] = None
    class Config:
        from_attributes = True

class FAQDetailOut(FAQListOut):
    content: str


class FAQPublicOut(FAQListOut):
    """Public FAQ schema with full content included (for list and detail responses)."""
    content: str


class FAQPublicListResponse(BaseModel):
    """Paginated response for public FAQ list endpoint."""
    items: List[FAQPublicOut]
    meta: PaginationMeta