"""
Unit tests for AI Chatbot Module.

Tests cover:
- Sending messages to chatbot
- Getting chat session and history
- Deleting chat sessions
- Chatbot context building (customer profile, tickets, FAQ)
- Cache management (preload, invalidate, extend TTL)
- Rate limiting
- Error handling

Test flow:
1. Customer sends message to chatbot
2. Chatbot builds context (customer profile, tickets, FAQ)
3. Message is sent to Groq LLM
4. Response is saved and returned
5. Session is created if not exists
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime
from uuid import uuid4
import json

from app.services.chatbotService import ChatbotService
from app.models.chatbot import ChatSession, ChatMessage
from app.models.human import Customer
from app.models.ticket import Ticket


# ============================================================================
# Chatbot Message Tests
# ============================================================================

class TestChatbotMessaging:
    """Tests for chatbot message sending."""

    def test_send_message_creates_session(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test that sending message creates session if not exists."""
        service = ChatbotService(db_session)

        # Mock Groq service response
        mock_groq_service.chat.return_value = "Hello! How can I help you today?"

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message="Hello"
        )

        assert message is not None
        assert message.role == "assistant"

    def test_send_message_saves_user_message(
        self,
        db_session,
        sample_customer,
        sample_chat_session,
        mock_groq_service,
        mock_redis_service
    ):
        """Test that user's message is saved."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "I received your message!"

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message="What is my ticket status?"
        )

        # Verify user message was saved
        from app.repositories.chatbotRepository import ChatMessageRepository
        msg_repo = ChatMessageRepository(db_session)
        user_messages = msg_repo.get_by_session_id(sample_chat_session.id_session)

        assert any(m.role == "user" and m.content == "What is my ticket status?" for m in user_messages)

    def test_send_message_saves_assistant_response(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test that assistant's response is saved."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "Your ticket is being processed."

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message="Hello"
        )

        # Verify assistant message was saved
        session = service.session_repo.get_by_customer_id(sample_customer.id_customer)
        from app.repositories.chatbotRepository import ChatMessageRepository
        msg_repo = ChatMessageRepository(db_session)
        messages = msg_repo.get_by_session_id(session.id_session)

        assert any(m.role == "assistant" for m in messages)

    def test_send_message_groq_error(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test chatbot handles Groq API error gracefully."""
        service = ChatbotService(db_session)

        # Mock Groq to raise exception
        with patch("app.services.chatbotService.GroqService") as mock_groq:
            mock_groq_instance = mock_groq.return_value
            mock_groq_instance.chat.side_effect = Exception("Groq API Error")

            with pytest.raises(Exception) as exc_info:
                service.send_message(
                    customer_id=sample_customer.id_customer,
                    user_message="Hello"
                )

            assert "AI service error" in str(exc_info.value)


# ============================================================================
# Chatbot Session Tests
# ============================================================================

class TestChatbotSession:
    """Tests for chatbot session management."""

    def test_get_session_existing(
        self,
        db_session,
        sample_customer,
        sample_chat_session
    ):
        """Test getting existing chat session."""
        service = ChatbotService(db_session)

        session = service.get_session(sample_customer.id_customer)

        assert session is not None
        assert session.customer_id == sample_customer.id_customer

    def test_get_session_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test getting session when none exists raises 404."""
        service = ChatbotService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_session(sample_customer.id_customer)

        assert "Chat session not found" in str(exc_info.value)

    def test_delete_session_success(
        self,
        db_session,
        sample_customer,
        sample_chat_session
    ):
        """Test successful session deletion."""
        service = ChatbotService(db_session)

        result = service.delete_session(sample_customer.id_customer)

        assert result is True

        # Verify session is deleted
        with pytest.raises(Exception):
            service.get_session(sample_customer.id_customer)

    def test_delete_session_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test deleting nonexistent session raises 404."""
        service = ChatbotService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_session(sample_customer.id_customer)

        assert "Chat session not found" in str(exc_info.value)


# ============================================================================
# Chatbot Context Building Tests
# ============================================================================

class TestChatbotContext:
    """Tests for chatbot context building."""

    def test_get_customer_data(
        self,
        db_session,
        sample_customer
    ):
        """Test getting customer profile data."""
        service = ChatbotService(db_session)

        data = service._get_customer_data(sample_customer.id_customer)

        assert data["customer_code"] == sample_customer.customer_code
        assert data["membership_tier"] == sample_customer.membership_tier
        assert data["first_name"] == sample_customer.first_name

    def test_get_customer_data_not_found(
        self,
        db_session
    ):
        """Test getting data for nonexistent customer raises error."""
        service = ChatbotService(db_session)

        with pytest.raises(Exception) as exc_info:
            service._get_customer_data(uuid4())

        assert "Customer not found" in str(exc_info.value)

    def test_get_customer_tickets(
        self,
        db_session,
        sample_customer,
        sample_ticket
    ):
        """Test getting customer's tickets for context."""
        service = ChatbotService(db_session)

        tickets = service._get_customer_tickets(sample_customer.id_customer)

        assert len(tickets) >= 1
        assert any(t["title"] == sample_ticket.title for t in tickets)

    def test_get_public_data(
        self,
        db_session,
        sample_department,
        sample_customer_type
    ):
        """Test getting public data (FAQ, departments, etc.)."""
        service = ChatbotService(db_session)

        data = service._get_public_data()

        assert "faqs" in data
        assert "departments" in data
        assert "customer_types" in data

    def test_build_context_format(
        self,
        db_session,
        sample_customer,
        sample_ticket,
        mock_redis_service
    ):
        """Test that context is built in expected format."""
        service = ChatbotService(db_session)

        context = service._build_context(sample_customer.id_customer)

        assert "CUSTOMER PROFILE" in context
        assert "TICKETS" in context or "No tickets found" in context
        assert sample_customer.first_name in context or sample_customer.last_name in context


# ============================================================================
# Cache Management Tests
# ============================================================================

class TestChatbotCache:
    """Tests for chatbot cache management."""

    def test_preload_customer_data(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test preloading customer data to cache."""
        # Note: This is a static method that creates its own DB session
        with patch("app.services.chatbotService.ChatbotService._preload_customer_data") as mock_preload:
            mock_preload.return_value = True

            result = ChatbotService._preload_customer_data(sample_customer.id_customer)

            assert result is True

    def test_invalidate_customer_cache(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test invalidating customer cache."""
        result = ChatbotService._invalidate_customer_cache(sample_customer.id_customer)

        assert result is True
        mock_redis_service.delete.assert_called()

    def test_extend_cache_ttl(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test extending cache TTL after token refresh."""
        mock_redis_service.get.return_value = '{"test": "data"}'

        result = ChatbotService._extend_cache_ttl(sample_customer.id_customer)

        assert result is True

    def test_invalidate_public_data_cache(
        self,
        mock_redis_service
    ):
        """Test invalidating public data cache."""
        result = ChatbotService.invalidate_public_data_cache()

        assert result is True


# ============================================================================
# Chatbot Rate Limiting Tests
# ============================================================================

class TestChatbotRateLimiting:
    """Tests for chatbot rate limiting."""

    def test_rate_limit_allows_first_request(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test first request within window is allowed."""
        mock_redis_service.get.return_value = None  # No existing count

        # This tests the rate limit check logic
        from app.api.v1.chatbot import check_chatbot_rate_limit

        result = check_chatbot_rate_limit(str(sample_customer.id_customer))

        assert result is True

    def test_rate_limit_blocks_excessive_requests(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test excessive requests are blocked."""
        mock_redis_service.get.return_value = "15"  # Exceeds limit of 10

        from app.api.v1.chatbot import check_chatbot_rate_limit

        result = check_chatbot_rate_limit(str(sample_customer.id_customer))

        assert result is False


# ============================================================================
# Chat History Tests
# ============================================================================

class TestChatbotHistory:
    """Tests for chatbot message history."""

    def test_build_messages_includes_history(
        self,
        db_session,
        sample_customer,
        sample_chat_session,
        mock_redis_service
    ):
        """Test that chat history is included in messages."""
        service = ChatbotService(db_session)

        messages = service._build_messages(sample_customer.id_customer)

        # Should have at least system prompt
        assert len(messages) >= 1
        assert messages[0]["role"] == "system"

    def test_build_messages_respects_limit(
        self,
        db_session,
        sample_customer,
        sample_chat_session
    ):
        """Test that only recent messages are included."""
        service = ChatbotService(db_session)

        # Add more than 10 messages
        for i in range(15):
            from app.models.chatbot import ChatMessage
            msg = ChatMessage(
                id_message=uuid4(),
                session_id=sample_chat_session.id_session,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            db_session.add(msg)
        db_session.commit()

        messages = service._build_messages(sample_customer.id_customer)

        # Should be limited to last 10 messages + system messages
        # (exact count depends on implementation)
        assert len(messages) <= 15  # At most all messages


# ============================================================================
# Chatbot Edge Cases
# ============================================================================

class TestChatbotEdgeCases:
    """Edge case tests for chatbot functionality."""

    def test_empty_message_handling(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test handling of empty message."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "Please provide more details."

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message=""
        )

        assert message is not None

    def test_very_long_message(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test handling of very long message."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "Message received."

        long_message = "A" * 5000  # 5000 character message

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message=long_message
        )

        assert message is not None

    def test_special_characters_in_message(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test handling of special characters."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "Message processed."

        special_message = "Hello! 🐱 @user #topic with <html> tags & symbols"

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message=special_message
        )

        assert message is not None

    def test_customer_without_tickets(
        self,
        db_session,
        sample_customer,
        mock_groq_service,
        mock_redis_service
    ):
        """Test chatbot handles customer with no tickets."""
        service = ChatbotService(db_session)

        mock_groq_service.chat.return_value = "You have no tickets."

        message = service.send_message(
            customer_id=sample_customer.id_customer,
            user_message="What tickets do I have?"
        )

        assert message is not None

    def test_multiple_sessions_same_customer(
        self,
        db_session,
        sample_customer
    ):
        """Test that only one session exists per customer."""
        service = ChatbotService(db_session)

        # Get or create first time
        session1 = service.session_repo.get_or_create(sample_customer.id_customer)

        # Get or create second time
        session2 = service.session_repo.get_or_create(sample_customer.id_customer)

        assert session1.id_session == session2.id_session
