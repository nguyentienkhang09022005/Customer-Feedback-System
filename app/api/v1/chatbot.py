from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.chatbotService import ChatbotService
from app.schemas.chatbot import (
    SendMessageRequest,
    SendMessageResponse,
    ChatHistoryResponse,
    SessionResponse,
    DeleteSessionResponse,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_customer
from app.models.human import Human, Customer

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/message", response_model=APIResponse[SendMessageResponse])
def send_message(
    data: SendMessageRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Send a message to the chatbot and get AI response."""
    try:
        service = ChatbotService(db)
        message = service.send_message(current_customer.id_customer, data.message)
        return APIResponse(
            status=True,
            code=200,
            message="Message sent successfully",
            data=SendMessageResponse(message=message)
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/history", response_model=APIResponse[ChatHistoryResponse])
def get_history(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer's chat history."""
    try:
        service = ChatbotService(db)
        session = service.get_history(current_customer.id_customer)
        return APIResponse(
            status=True,
            code=200,
            message="Chat history retrieved",
            data=ChatHistoryResponse(
                session=session,
                total_messages=len(session.messages)
            )
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/session", response_model=APIResponse[SessionResponse])
def get_or_create_session(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer's chat session."""
    try:
        service = ChatbotService(db)
        session = service.get_or_create_session(current_customer.id_customer)
        return APIResponse(
            status=True,
            code=200,
            message="Session retrieved successfully" if session.messages else "Empty session",
            data=SessionResponse(session=session)
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/session", response_model=APIResponse[DeleteSessionResponse])
def delete_session(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Delete customer's chat session."""
    try:
        service = ChatbotService(db)
        service.delete_session(current_customer.id_customer)
        return APIResponse(
            status=True,
            code=200,
            message="Session deleted successfully",
            data=DeleteSessionResponse(message="Session deleted successfully")
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)