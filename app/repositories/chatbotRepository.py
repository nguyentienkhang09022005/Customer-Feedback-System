from sqlalchemy.orm import Session
from app.models.chatbot import ChatSession, ChatMessage
from typing import Optional, List
import uuid


class ChatSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_customer_id(self, customer_id: uuid.UUID) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(
            ChatSession.customer_id == customer_id
        ).first()

    def create(self, customer_id: uuid.UUID) -> ChatSession:
        session = ChatSession(customer_id=customer_id)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_or_create(self, customer_id: uuid.UUID) -> ChatSession:
        session = self.get_by_customer_id(customer_id)
        if not session:
            session = self.create(customer_id)
        return session

    def delete(self, customer_id: uuid.UUID) -> bool:
        session = self.get_by_customer_id(customer_id)
        if session:
            self.db.delete(session)
            self.db.commit()
            return True
        return False


class ChatMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_message(self, session_id: uuid.UUID, role: str, content: str) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_by_session_id(self, session_id: uuid.UUID) -> List[ChatMessage]:
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()

    def get_message_count(self, session_id: uuid.UUID) -> int:
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()
