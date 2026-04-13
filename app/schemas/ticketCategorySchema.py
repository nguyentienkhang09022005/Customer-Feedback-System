from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class TicketCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: Optional[bool] = True
    id_department: UUID
    auto_assign: Optional[bool] = True


class TicketCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    id_department: Optional[UUID] = None
    auto_assign: Optional[bool] = None


class TicketCategoryOut(BaseModel):
    id_category: UUID
    name: str
    description: Optional[str]
    is_active: bool
    id_department: UUID
    auto_assign: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketCategoryWithTemplatesOut(TicketCategoryOut):
    templates: List["TicketTemplateOut"] = []

    class Config:
        from_attributes = True


class TicketTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    id_category: Optional[UUID] = None
    id_author: Optional[UUID] = None
    is_active: Optional[bool] = True
    fields_config: dict


class TicketTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    id_category: Optional[UUID] = None
    is_active: Optional[bool] = None
    fields_config: Optional[dict] = None


class TicketTemplateOut(BaseModel):
    id_template: UUID
    version: int
    name: str
    description: Optional[str]
    fields_config: dict
    id_category: Optional[UUID] = None
    id_author: Optional[UUID] = None
    is_active: bool
    is_deleted: bool
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketTemplateDetailOut(TicketTemplateOut):
    category_name: Optional[str] = None
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


TicketCategoryWithTemplatesOut.model_rebuild()