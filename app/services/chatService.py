from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.messageRepository import MessageRepository
from app.schemas.chatSchema import (
    MessageCreate,
    MessageOut,
    MessageType,
    UserBriefOut
)
from app.models.interaction import Message
from app.models.human import Human
from typing import List, Tuple, Optional
import uuid

from app.services.auditLogService import AuditLogService

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.message_repo = MessageRepository(db)
        self.audit_service = AuditLogService(db)

    def send_message(
        self,
        ticket_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
        message_type: MessageType = MessageType.TEXT
    ) -> MessageOut:
        self.validate_participant(ticket_id, sender_id)
        
        message = self.message_repo.create_message(
            ticket_id=ticket_id,
            sender_id=sender_id,
            content=content,
            message_type=message_type.value
        )
        
        return self._to_message_out(message)

    def get_chat_history(
        self,
        ticket_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[MessageOut], int]:
        messages, total = self.message_repo.get_messages_by_ticket(ticket_id, page, limit)
        message_outs = [self._to_message_out(m) for m in messages]
        return message_outs, total

    def validate_participant(self, ticket_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        ticket = self.message_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket không tồn tại!")
        
        if ticket.id_customer != user_id and ticket.id_employee != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập cuộc trò chuyện này!")
        
        return True

    def mark_messages_read(self, ticket_id: uuid.UUID, user_id: uuid.UUID) -> None:
        self.validate_participant(ticket_id, user_id)
        self.message_repo.mark_as_read(ticket_id, user_id)

    def get_unread_count(self, ticket_id: uuid.UUID, user_id: uuid.UUID) -> int:
        self.validate_participant(ticket_id, user_id)
        return self.message_repo.get_unread_count(ticket_id, user_id)

    def get_conversations_for_employee(
        self,
        employee_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List, int]:
        return self.message_repo.get_conversations_for_employee(employee_id, page, limit)

    def get_conversations_for_customer(
        self,
        customer_id: uuid.UUID,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List, int]:
        return self.message_repo.get_conversations_for_customer(customer_id, page, limit)

    def _to_message_out(self, message: Message) -> MessageOut:
        sender = None
        if message.id_sender:
            sender = self.db.query(Human).filter(Human.id == message.id_sender).first()
        
        sender_out = None
        if sender:
            sender_out = UserBriefOut(
                id=sender.id,
                first_name=sender.first_name,
                last_name=sender.last_name,
                avatar=sender.avatar
            )
        
        return MessageOut(
            id_message=message.id_message,
            content=message.message,
            message_type=MessageType(message.message_type),
            is_read=message.is_read,
            created_at=message.created_at,
            sender=sender_out
        )

    def delete_message(self, message_id: uuid.UUID, employee_id: uuid.UUID) -> None:
        message = self.message_repo.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại!")

        if message.is_deleted:
            raise HTTPException(status_code=400, detail="Tin nhắn đã bị xóa!")

        old_data = {
            "content": message.message,
            "message_type": message.message_type,
            "is_deleted": False
        }

        new_data = {
            "content": message.message,
            "is_deleted": True
        }

        self.audit_service.log_action(
            log_type="MESSAGE",
            action="DELETE",
            old_data=old_data,
            new_data=new_data,
            id_reference=message.id_message,
            id_employee=employee_id
        )

        self.message_repo.soft_delete_message(message_id)

    def update_message(self, ticket_id: uuid.UUID, message_id: uuid.UUID, employee_id: uuid.UUID,
                       new_content: str) -> MessageOut:
        message = self.message_repo.get_message_by_id(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Tin nhắn không tồn tại!")

        if message.id_ticket != ticket_id:
            raise HTTPException(status_code=400, detail="Tin nhắn không thuộc ticket này!")

        if message.is_deleted:
            raise HTTPException(status_code=400, detail="Không thể sửa tin nhắn đã bị xóa!")

        old_data = {"content": message.message}
        new_data = {"content": new_content}

        self.audit_service.log_action(
            log_type="MESSAGE",
            action="UPDATE",
            old_data=old_data,
            new_data=new_data,
            id_reference=message.id_message,
            id_employee=employee_id
        )

        message.message = new_content
        self.db.commit()
        self.db.refresh(message)

        return self._to_message_out(message)