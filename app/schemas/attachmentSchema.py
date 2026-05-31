from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class AttachmentResponse(BaseModel):
    id_attachment: UUID
    attach_name: str
    attach_type: Optional[str] = None
    attach_extension: Optional[str] = None
    url: str
    file_size: Optional[int] = None
    storage_type: Optional[str] = None
    public_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    reference_type: Optional[str] = None
    id_reference: Optional[UUID] = None
    id_uploader: UUID
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttachmentUploadResponse(BaseModel):
    id_attachment: UUID
    attach_name: str
    url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    message: str

    class Config:
        from_attributes = True


class AttachmentDeleteResponse(BaseModel):
    id_attachment: UUID
    message: str

    class Config:
        from_attributes = True


class AttachmentListResponse(BaseModel):
    attachments: List[AttachmentResponse]
    total: int

    class Config:
        from_attributes = True


class AttachmentCleanupResponse(BaseModel):
    deleted_count: int
    message: str

    class Config:
        from_attributes = True
