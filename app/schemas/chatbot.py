from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class ChatMessageSchema(BaseModel):
    id_message: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionSchema(BaseModel):
    id_session: UUID
    customer_id: UUID
    messages: List[ChatMessageSchema] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    message: ChatMessageSchema


class ChatHistoryResponse(BaseModel):
    session: ChatSessionSchema
    total_messages: int


class SessionResponse(BaseModel):
    session: Optional[ChatSessionSchema] = None
    message: str = "Session not found" if session is None else "Session retrieved successfully" if session.messages else "Empty session" if session else ""


class DeleteSessionResponse(BaseModel):
    message: str