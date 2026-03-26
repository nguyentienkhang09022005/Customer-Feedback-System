from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.chatService import ChatService
from app.schemas.chatSchema import (
    MessageCreate,
    MessageOut,
    ChatHistoryOut,
    ConversationOut,
    UnreadCountOut,
    MessageType, MessageUpdate
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer
from app.models.human import Human, Customer, Employee

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/tickets/{ticket_id}/messages", response_model=APIResponse[ChatHistoryOut])
def get_chat_history(
    ticket_id: UUID,
    page: int = 1,
    limit: int = 20,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        service.validate_participant(ticket_id, current_user.id)
        messages, total = service.get_chat_history(ticket_id, page, limit)
        return APIResponse(
            status=True,
            code=200,
            message="Thành công",
            data=ChatHistoryOut(messages=messages, total=total, page=page, limit=limit)
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/tickets/{ticket_id}/messages", response_model=APIResponse[MessageOut])
def send_message(
    ticket_id: UUID,
    data: MessageCreate,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        message = service.send_message(ticket_id, current_user.id, data.content, data.message_type)
        return APIResponse(status=True, code=201, message="Gửi tin nhắn thành công", data=message)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/tickets/{ticket_id}/read", response_model=APIResponse)
def mark_messages_read(
    ticket_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        service.mark_messages_read(ticket_id, current_user.id)
        return APIResponse(status=True, code=200, message="Đã đánh dấu đã đọc")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/tickets/{ticket_id}/unread-count", response_model=APIResponse[UnreadCountOut])
def get_unread_count(
    ticket_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        count = service.get_unread_count(ticket_id, current_user.id)
        return APIResponse(
            status=True,
            code=200,
            message="Thành công",
            data=UnreadCountOut(ticket_id=ticket_id, unread_count=count)
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/conversations", response_model=APIResponse[List[ConversationOut]])
def get_conversations(
    page: int = 1,
    limit: int = 20,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        
        if isinstance(current_user, Employee):
            tickets, total = service.get_conversations_for_employee(current_user.id, page, limit)
        elif isinstance(current_user, Customer):
            tickets, total = service.get_conversations_for_customer(current_user.id, page, limit)
        else:
            return APIResponse(status=False, code=403, message="Không có quyền truy cập")
        
        conversations = []
        for ticket in tickets:
            last_message = None
            messages, _ = service.get_chat_history(ticket.id_ticket, 1, 1)
            if messages:
                last_message = messages[0]
            
            unread_count = service.get_unread_count(ticket.id_ticket, current_user.id)
            
            customer = db.query(Customer).filter(Customer.id == ticket.id_customer).first()
            employee = None
            if ticket.id_employee:
                emp = db.query(Employee).filter(Employee.id == ticket.id_employee).first()
                if emp:
                    employee = emp
            
            conv = ConversationOut(
                id_ticket=ticket.id_ticket,
                ticket_title=ticket.title,
                customer=customer,
                employee=employee,
                last_message=last_message,
                unread_count=unread_count
            )
            conversations.append(conv)
        
        return APIResponse(status=True, code=200, message="Thành công", data=conversations)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/tickets/{ticket_id}/messages/{message_id}", response_model=APIResponse)
def delete_message(
        ticket_id: UUID,
        message_id: UUID,
        current_employee: Employee = Depends(get_current_employee),
        db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)

        service.validate_participant(ticket_id, current_employee.id)

        service.delete_message(message_id=message_id, employee_id=current_employee.id)

        return APIResponse(
            status=True,
            code=200,
            message="Đã xóa tin nhắn thành công và ghi nhận lịch sử hệ thống!"
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.put("/tickets/{ticket_id}/messages/{message_id}", response_model=APIResponse[MessageOut])
def update_message(
        ticket_id: UUID,
        message_id: UUID,
        data: MessageUpdate,
        current_employee: Employee = Depends(get_current_employee),
        db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)

        service.validate_participant(ticket_id, current_employee.id)

        updated_msg = service.update_message(
            ticket_id=ticket_id,
            message_id=message_id,
            employee_id=current_employee.id,
            new_content=data.content
        )

        return APIResponse(
            status=True,
            code=200,
            message="Cập nhật tin nhắn thành công!",
            data=updated_msg
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)