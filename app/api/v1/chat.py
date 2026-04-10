from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.core.pagination import paginate
from app.api.dependencies import get_db, get_current_user, get_current_employee, get_current_customer
from app.models.human import Human, Customer, Employee

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/tickets/{ticket_id}/messages", response_model=APIResponse[ChatHistoryOut])
def get_chat_history(
    ticket_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = ChatService(db)
        service.validate_participant(ticket_id, current_user.id)
        
        from app.models.interaction import Message
        query = db.query(Message).filter(Message.id_ticket == ticket_id).order_by(Message.created_at.desc())
        messages, meta = paginate(query, page, limit)
        messages = [service._to_message_out(m) for m in messages]
        
        return APIResponse(
            status=True,
            code=200,
            message="Thành công",
            data=ChatHistoryOut(messages=messages, meta=meta)
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/tickets/{ticket_id}/messages", response_model=APIResponse[MessageOut], include_in_schema=False)
def send_message(
    ticket_id: str,
    data: MessageCreate,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    [HIDDEN] Vui lòng sử dụng Socket.IO 'send_message' event để gửi tin nhắn.
    API này đã bị ẩn khỏi tài liệu Swagger.
    """
    # Check if ticket is closed
    from app.services.ticketService import TicketService
    ticket_service = TicketService(db)
    ticket = ticket_service.get_ticket(ticket_id)
    if ticket and ticket.status == "Closed":
        raise HTTPException(status_code=400, detail="Ticket is closed. Cannot send messages.")
    
    try:
        service = ChatService(db)
        message = service.send_message(ticket_id, current_user.id, data.content, data.message_type)
        return APIResponse(
            status=True,
            code=201,
            message="Gửi tin nhắn thành công (đã ẩn - vui lòng dùng Socket.IO)",
            data=message
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/tickets/{ticket_id}/read", response_model=APIResponse)
def mark_messages_read(
    ticket_id: str,
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
    ticket_id: str,
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
        
        # Pre-fetch all related data in bulk to avoid N+1 queries
        ticket_ids = [t.id_ticket for t in tickets]
        customer_ids = list(set([t.id_customer for t in tickets if t.id_customer]))
        employee_ids = list(set([t.id_employee for t in tickets if t.id_employee]))
        
        # Bulk query customers
        customers = {c.id: c for c in db.query(Customer).filter(Customer.id.in_(customer_ids)).all()} if customer_ids else {}
        # Bulk query employees
        employees = {e.id: e for e in db.query(Employee).filter(Employee.id.in_(employee_ids)).all()} if employee_ids else {}
        
        # Bulk query last messages (one query per page instead of N queries)
        from app.models.interaction import Message
        last_messages_map = {}
        for tid in ticket_ids:
            last_msg = db.query(Message).filter(
                Message.id_ticket == tid,
                Message.is_deleted == False
            ).order_by(Message.created_at.desc()).first()
            last_messages_map[tid] = last_msg
        
        conversations = []
        for ticket in tickets:
            last_message = None
            last_msg = last_messages_map.get(ticket.id_ticket)
            if last_msg:
                last_message = service._to_message_out(last_msg)
            
            unread_count = service.get_unread_count(ticket.id_ticket, current_user.id)
            
            customer = customers.get(ticket.id_customer)
            employee = employees.get(ticket.id_employee) if ticket.id_employee else None
            
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