from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.chatbotRepository import ChatSessionRepository, ChatMessageRepository
from app.repositories.faqRepository import FAQRepository
from app.repositories.departmentRepository import DepartmentRepository
from app.repositories.customerTypeRepository import CustomerTypeRepository
from app.repositories.ticketCategoryRepository import TicketCategoryRepository
from app.repositories.ticketRepository import TicketRepository
from app.repositories.ticketTemplateRepository import TicketTemplateRepository
from app.repositories.slaRepository import SLAPolicyRepository
from app.models.human import Customer
from app.models.ticket import Ticket
from app.schemas.chatbot import ChatMessageSchema, ChatSessionSchema
from app.services.groqService import GroqService
from app.services.redisService import redis_service
from app.core.config import settings
from typing import List, Dict, Any
import uuid
import logging
import json

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a customer support assistant for this feedback system.
You can help customers with:
- Their own account information (membership tier, customer type, profile)
- Their tickets (status, history, details)
- FAQ and common questions
- Department and service information
- Ticket categories and templates
- SLA policies

You CANNOT:
- Access other customers' information
- Access employee private data
- Reveal any private information about other users
- Make up information that is not provided in the context

Only discuss the current customer's own data when they specifically ask about it.
If you don't know something, say you don't know rather than making up information.
"""

# Cache key and TTL for chatbot public data
CHATBOT_PUBLIC_DATA_CACHE_KEY = "chatbot:public_data"
CHATBOT_PUBLIC_DATA_CACHE_TTL = 600  # 10 minutes

# Cache key and TTL for customer-specific data (per customer)
CHATBOT_CUSTOMER_PROFILE_KEY = "chatbot:customer:{customer_id}:profile"
CHATBOT_CUSTOMER_TICKETS_KEY = "chatbot:customer:{customer_id}:tickets"


class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
        self.faq_repo = FAQRepository(db)
        self.dept_repo = DepartmentRepository(db)
        self.customer_type_repo = CustomerTypeRepository(db)
        self.ticket_category_repo = TicketCategoryRepository(db)
        self.ticket_repo = TicketRepository(db)
        self.template_repo = TicketTemplateRepository(db)
        self.sla_repo = SLAPolicyRepository(db)
        self.groq_service = GroqService()

    def _get_customer_data(self, customer_id: uuid.UUID) -> Dict[str, Any]:
        """Get customer's own data for context."""
        customer = self.db.query(Customer).filter(Customer.id_customer == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {
            "customer_code": customer.customer_code,
            "membership_tier": customer.membership_tier,
            "timezone": customer.timezone,
            "customer_type": customer.customer_type,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
        }

    def _get_customer_tickets(self, customer_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get customer's tickets for context."""
        tickets = self.ticket_repo.get_by_customer(customer_id, include_closed=True, limit=100)
        return [
            {
                "ticket_id": str(t.id_ticket),
                "title": t.title,
                "status": t.status,
                "severity": t.severity,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tickets
        ]

    def _get_customer_data_cached(self, customer_id: uuid.UUID) -> Dict[str, Any]:
        """Get customer's profile data with Redis caching."""
        cache_key = CHATBOT_CUSTOMER_PROFILE_KEY.format(customer_id=str(customer_id))

        # Try cache first
        cached = redis_service.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to decode cached customer profile, fetching from DB")

        # Fetch from DB
        data = self._get_customer_data(customer_id)

        # Cache with TTL = token expiry
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_service.set_with_expiry(cache_key, json.dumps(data), ttl)

        return data

    def _get_customer_tickets_cached(self, customer_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get customer's tickets with Redis caching."""
        cache_key = CHATBOT_CUSTOMER_TICKETS_KEY.format(customer_id=str(customer_id))

        # Try cache first
        cached = redis_service.get(cache_key)
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to decode cached customer tickets, fetching from DB")

        # Fetch from DB
        data = self._get_customer_tickets(customer_id)

        # Cache with TTL = token expiry
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        redis_service.set_with_expiry(cache_key, json.dumps(data), ttl)

        return data

    # Track in-progress preloads to prevent duplicate work
    _preload_in_progress: Dict[str, bool] = {}

    @staticmethod
    def _preload_customer_data(customer_id: uuid.UUID, max_retries: int = 3, base_delay: float = 0.5) -> bool:
        """Preload customer data to Redis cache with retry logic.

        Returns True if successful, False otherwise.
        """
        from app.db.session import SessionLocal
        import time

        customer_id_str = str(customer_id)

        # Deduplication: skip if preload already in progress for this customer
        if ChatbotService._preload_in_progress.get(customer_id_str):
            return True

        ChatbotService._preload_in_progress[customer_id_str] = True

        try:
            last_error = None
            for attempt in range(max_retries):
                db = SessionLocal()
                try:
                    service = ChatbotService(db)

                    # Get and cache profile
                    profile = service._get_customer_data(customer_id)
                    profile_key = CHATBOT_CUSTOMER_PROFILE_KEY.format(customer_id=str(customer_id))
                    ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
                    redis_service.set_with_expiry(profile_key, json.dumps(profile), ttl)
                    logger.info(f"Preloaded profile cache for customer {customer_id}")

                    # Get and cache tickets
                    tickets = service._get_customer_tickets(customer_id)
                    tickets_key = CHATBOT_CUSTOMER_TICKETS_KEY.format(customer_id=str(customer_id))
                    redis_service.set_with_expiry(tickets_key, json.dumps(tickets), ttl)
                    logger.info(f"Preloaded tickets cache for customer {customer_id}")

                    return True  # Success

                except Exception as e:
                    last_error = e
                    logger.warning(f"Preload attempt {attempt + 1}/{max_retries} failed for {customer_id}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))  # Exponential backoff
                finally:
                    db.close()

            # All retries failed
            logger.error(f"PRELOAD FAILED ALL {max_retries} RETRIES for {customer_id}: {last_error}")
            return False

        finally:
            # Always cleanup the in-progress flag
            ChatbotService._preload_in_progress.pop(customer_id_str, None)

    @staticmethod
    def _invalidate_customer_cache(customer_id: uuid.UUID) -> bool:
        """Invalidate customer cache on logout."""
        profile_key = CHATBOT_CUSTOMER_PROFILE_KEY.format(customer_id=str(customer_id))
        tickets_key = CHATBOT_CUSTOMER_TICKETS_KEY.format(customer_id=str(customer_id))

        redis_service.delete(profile_key)
        redis_service.delete(tickets_key)
        logger.info(f"Invalidated cache for customer {customer_id}")
        return True

    @staticmethod
    def _extend_cache_ttl(customer_id: uuid.UUID) -> bool:
        """Extend cache TTL when token is refreshed. Prevents cache from expiring before token."""
        ttl = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        profile_key = CHATBOT_CUSTOMER_PROFILE_KEY.format(customer_id=str(customer_id))
        tickets_key = CHATBOT_CUSTOMER_TICKETS_KEY.format(customer_id=str(customer_id))

        # Re-set with new TTL (Redis will update expiry)
        profile_data = redis_service.get(profile_key)
        tickets_data = redis_service.get(tickets_key)

        if profile_data:
            redis_service.set_with_expiry(profile_key, profile_data, ttl)
        if tickets_data:
            redis_service.set_with_expiry(tickets_key, tickets_data, ttl)

        logger.info(f"Extended cache TTL for customer {customer_id}")
        return True

    def _get_public_data(self) -> Dict[str, Any]:
        """Get all public data for context with Redis caching."""
        # Try to get from cache first
        cached = redis_service.get(CHATBOT_PUBLIC_DATA_CACHE_KEY)
        if cached:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to decode cached public data, fetching from DB")

        # Fetch from database
        faqs = self.faq_repo.get_public_articles()
        departments = self.dept_repo.get_active_all()
        customer_types = self.customer_type_repo.get_all()
        ticket_categories = self.ticket_category_repo.get_active_all()
        templates = self.template_repo.get_active_templates() if hasattr(self.template_repo, 'get_active_templates') else []
        sla_policies = self.sla_repo.get_active_all() if hasattr(self.sla_repo, 'get_active_all') else []

        result = {
            "faqs": [
                {"title": f.title, "content": f.content}
                for f in faqs
            ],
            "departments": [
                {"name": d.name, "description": d.description}
                for d in departments
            ],
            "customer_types": [
                {"type_name": ct.type_name, "description": ct.description}
                for ct in customer_types
            ],
            "ticket_categories": [
                {"name": c.name, "description": c.description}
                for c in ticket_categories
            ],
            "templates": [
                {"name": t.name, "description": t.description}
                for t in templates
            ] if templates else [],
            "sla_policies": [
                {"policy_name": p.policy_name, "severity": p.severity, "max_resolution_days": p.max_resolution_days}
                for p in sla_policies
            ] if sla_policies else [],
        }

        # Cache the result
        redis_service.set_with_expiry(
            CHATBOT_PUBLIC_DATA_CACHE_KEY,
            json.dumps(result),
            CHATBOT_PUBLIC_DATA_CACHE_TTL
        )

        return result

    def _build_context(self, customer_id: uuid.UUID) -> str:
        """Build context string from customer's data and public data."""
        customer_data = self._get_customer_data_cached(customer_id)
        customer_tickets = self._get_customer_tickets_cached(customer_id)
        public_data = self._get_public_data()

        context = "=== CUSTOMER PROFILE ===\n"
        context += f"Name: {customer_data['first_name']} {customer_data['last_name']}\n"
        context += f"Customer Code: {customer_data['customer_code']}\n"
        context += f"Membership Tier: {customer_data['membership_tier']}\n"
        context += f"Customer Type: {customer_data['customer_type']}\n"
        context += f"Timezone: {customer_data['timezone']}\n"

        context += "\n=== THIS CUSTOMER'S TICKETS ===\n"
        if customer_tickets:
            for t in customer_tickets:
                context += f"- [{t['status']}] {t['title']} (ID: {t['ticket_id']}, Created: {t['created_at']})\n"
        else:
            context += "No tickets found.\n"

        context += "\n=== PUBLIC FAQ ===\n"
        if public_data['faqs']:
            for faq in public_data['faqs'][:10]:  # Limit to 10 FAQs
                context += f"Q: {faq['title']}\nA: {faq['content']}\n"
        else:
            context += "No FAQs available.\n"

        context += "\n=== DEPARTMENTS ===\n"
        if public_data['departments']:
            for dept in public_data['departments']:
                context += f"- {dept['name']}: {dept['description']}\n"
        else:
            context += "No departments available.\n"

        context += "\n=== CUSTOMER TYPES ===\n"
        if public_data['customer_types']:
            for ct in public_data['customer_types']:
                context += f"- {ct['type_name']}: {ct['description']}\n"
        else:
            context += "No customer types available.\n"

        context += "\n=== TICKET CATEGORIES ===\n"
        if public_data['ticket_categories']:
            for cat in public_data['ticket_categories']:
                context += f"- {cat['name']}: {cat['description']}\n"
        else:
            context += "No ticket categories available.\n"

        return context

    def _build_messages(self, customer_id: uuid.UUID) -> List[Dict[str, str]]:
        """Build messages list for Groq API including full chat history."""
        session = self.session_repo.get_by_customer_id(customer_id)
        if not session:
            return [{"role": "system", "content": SYSTEM_PROMPT}]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add context as a system message
        context = self._build_context(customer_id)
        messages.append({
            "role": "system",
            "content": f"=== CONTEXT (Only use this information about the customer) ===\n{context}"
        })

        # Add chat history (last 10 messages only)
        chat_messages = self.message_repo.get_by_session_id(session.id_session)[-10:]
        for msg in chat_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    def send_message(self, customer_id: uuid.UUID, user_message: str) -> ChatMessageSchema:
        """Send a message and get AI response."""
        # Get or create session
        session = self.session_repo.get_or_create(customer_id)

        # Save user's message
        user_msg = self.message_repo.add_message(
            session_id=session.id_session,
            role="user",
            content=user_message
        )

        # Build messages for Groq
        messages = self._build_messages(customer_id)

        # Get AI response
        try:
            ai_content = self.groq_service.chat(messages)
        except Exception as e:
            logger.error(f"Groq API error: {str(e)}")
            raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")

        # Save AI's response
        ai_msg = self.message_repo.add_message(
            session_id=session.id_session,
            role="assistant",
            content=ai_content
        )

        return ChatMessageSchema(
            id_message=ai_msg.id_message,
            role=ai_msg.role,
            content=ai_msg.content,
            created_at=ai_msg.created_at
        )

    def get_session(self, customer_id: uuid.UUID) -> ChatSessionSchema:
        """Get existing session. Raises 404 if not found."""
        session = self.session_repo.get_by_customer_id(customer_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")

        messages = self.message_repo.get_by_session_id(session.id_session)

        return ChatSessionSchema(
            id_session=session.id_session,
            customer_id=session.customer_id,
            messages=[
                ChatMessageSchema(
                    id_message=m.id_message,
                    role=m.role,
                    content=m.content,
                    created_at=m.created_at
                )
                for m in messages
            ],
            created_at=session.created_at,
            updated_at=session.updated_at
        )

    def delete_session(self, customer_id: uuid.UUID) -> bool:
        """Delete customer's chat session."""
        success = self.session_repo.delete(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return True

    @staticmethod
    def invalidate_public_data_cache() -> bool:
        """Invalidate the cached public data. Call this when admin updates FAQ, Department, etc."""
        return redis_service.delete(CHATBOT_PUBLIC_DATA_CACHE_KEY)
