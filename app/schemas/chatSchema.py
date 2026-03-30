from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from app.schemas.paginationSchema import PaginationMeta


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"


class MessageCreate(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT


class UserBriefOut(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id_message: UUID
    content: str
    message_type: MessageType
    is_read: bool
    created_at: datetime
    sender: Optional[UserBriefOut] = None

    class Config:
        from_attributes = True


class ChatHistoryOut(BaseModel):
    messages: List[MessageOut]
    meta: PaginationMeta


class ConversationOut(BaseModel):
    id_ticket: UUID
    ticket_title: str
    customer: UserBriefOut
    employee: Optional[UserBriefOut] = None
    last_message: Optional[MessageOut] = None
    unread_count: int = 0


class UnreadCountOut(BaseModel):
    ticket_id: UUID
    unread_count: int

class MessageUpdate(BaseModel):
    content: str