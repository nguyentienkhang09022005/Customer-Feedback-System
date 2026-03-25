from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.interaction import Message
from app.models.ticket import Ticket
from typing import List, Optional, Tuple
import uuid


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_message(
        self,
        ticket_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        message_type: str = "text"
    ) -> Message:
        message = Message(
            message=content,
            message_type=message_type,
            id_ticket=ticket_id,
            id_sender=sender_id
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_messages_by_ticket(
        self,
        ticket_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Message], int]:
        query = self.db.query(Message).filter(
            and_(
                Message.id_ticket == ticket_id,
                Message.is_deleted == False
            )
        )
        total = query.count()
        offset = (page - 1) * limit
        messages = query.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
        return messages, total

    def get_ticket_by_id(self, ticket_id: uuid.UUID) -> Optional[Ticket]:
        return self.db.query(Ticket).filter(Ticket.id_ticket == ticket_id).first()

    def mark_as_read(self, ticket_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.db.query(Message).filter(
            and_(
                Message.id_ticket == ticket_id,
                Message.id_sender != user_id,
                Message.is_read == False
            )
        ).update({"is_read": True})
        self.db.commit()

    def get_unread_count(self, ticket_id: uuid.UUID, user_id: uuid.UUID) -> int:
        return self.db.query(Message).filter(
            and_(
                Message.id_ticket == ticket_id,
                Message.id_sender != user_id,
                Message.is_read == False,
                Message.is_deleted == False
            )
        ).count()

    def get_conversations_for_employee(
        self,
        employee_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Ticket], int]:
        query = self.db.query(Ticket).filter(
            Ticket.id_employee == employee_id
        )
        total = query.count()
        offset = (page - 1) * limit
        tickets = query.order_by(Ticket.updated_at.desc()).offset(offset).limit(limit).all()
        return tickets, total

    def get_conversations_for_customer(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[Ticket], int]:
        query = self.db.query(Ticket).filter(
            Ticket.id_customer == customer_id
        )
        total = query.count()
        offset = (page - 1) * limit
        tickets = query.order_by(Ticket.updated_at.desc()).offset(offset).limit(limit).all()
        return tickets, total