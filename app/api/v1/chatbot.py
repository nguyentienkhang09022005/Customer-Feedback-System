from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.chatbotService import ChatbotService
from app.schemas.chatbot import (
    SendMessageRequest,
    SendMessageResponse,
    ChatHistoryResponse,
    DeleteSessionResponse,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_customer
from app.models.human import Human, Customer
from app.services.redisService import redis_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Rate limiting config
CHATBOT_RATE_LIMIT = 10  # Max messages per window
CHATBOT_RATE_WINDOW = 60  # Window in seconds (1 minute)


def check_chatbot_rate_limit(customer_id: str) -> bool:
    """Check if customer is within rate limit for chatbot messages.

    Returns True if allowed, False if rate limited.
    """
    key = f"ratelimit:chatbot:{customer_id}"

    try:
        current = redis_service.get(key)
        if current and int(current) >= CHATBOT_RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for customer {customer_id}")
            return False

        # Increment counter
        if current:
            redis_service.increment(key)
        else:
            # First request in window
            redis_service.set_with_expiry(key, "1", CHATBOT_RATE_WINDOW)

        return True
    except Exception as e:
        # If Redis fails, allow the request but log warning
        logger.warning(f"Rate limit check failed, allowing request: {e}")
        return True


@router.post("/message", response_model=APIResponse[SendMessageResponse])
def send_message(
    data: SendMessageRequest,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Send a message to the chatbot and get AI response."""
    # Rate limit check
    if not check_chatbot_rate_limit(str(current_customer.id_customer)):
        return APIResponse(
            status=False,
            code=429,
            message=f"Too many requests. Limit is {CHATBOT_RATE_LIMIT} messages per minute."
        )

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


@router.get("/session", response_model=APIResponse[ChatHistoryResponse])
def get_session(
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """Get customer's chat session. Returns 404 if no session exists."""
    try:
        service = ChatbotService(db)
        session = service.get_session(current_customer.id_customer)
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