import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4
from fastapi import HTTPException
from app.services.chatService import ChatService
from app.schemas.chatSchema import MessageType


class TestChatService:
    """Test ChatService with N+1 fixes"""

    def test_to_message_out_uses_sender_cache_to_avoid_n_plus_1(self):
        """Test _to_message_out uses sender_cache to avoid N+1 queries"""
        db = MagicMock()
        service = ChatService(db)
        
        # Create mock message
        sender_id = uuid4()
        mock_message = MagicMock()
        mock_message.id_message = uuid4()
        mock_message.message = "Test message"
        mock_message.message_type = "text"
        mock_message.is_read = False
        mock_message.created_at = MagicMock()
        mock_message.id_sender = sender_id
        
        # Create mock sender
        mock_sender = MagicMock()
        mock_sender.id = sender_id
        mock_sender.first_name = "John"
        mock_sender.last_name = "Doe"
        mock_sender.avatar = "avatar.jpg"
        
        # Pre-populated cache
        sender_cache = {sender_id: mock_sender}
        
        # Should NOT query database because sender is in cache
        with patch.object(service.db, 'query') as mock_query:
            result = service._to_message_out(mock_message, sender_cache)
        
        # Verify sender was NOT queried (cached)
        mock_query.assert_not_called()
        
        # Verify result
        assert result.message == "Test message"
        assert result.sender is not None
        assert result.sender.first_name == "John"
        assert result.sender.last_name == "Doe"

    def test_to_message_out_queries_db_when_sender_not_in_cache(self):
        """Test _to_message_out queries DB for sender when not in cache"""
        db = MagicMock()
        service = ChatService(db)
        
        sender_id = uuid4()
        mock_message = MagicMock()
        mock_message.id_message = uuid4()
        mock_message.message = "Test message"
        mock_message.message_type = "text"
        mock_message.is_read = False
        mock_message.created_at = MagicMock()
        mock_message.id_sender = sender_id
        
        mock_sender = MagicMock()
        mock_sender.id = sender_id
        mock_sender.first_name = "Jane"
        mock_sender.last_name = "Doe"
        mock_sender.avatar = "avatar2.jpg"
        
        # Empty cache - should trigger query
        sender_cache = {}
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_sender
        db.query.return_value = mock_query
        
        result = service._to_message_out(mock_message, sender_cache)
        
        # Verify DB was queried
        db.query.assert_called()

    def test_validate_participant_allows_customer_owning_ticket(self):
        """Test validate_participant allows customer who owns the ticket"""
        db = MagicMock()
        service = ChatService(db)
        
        ticket_id = uuid4()
        customer_id = uuid4()
        
        mock_ticket = MagicMock()
        mock_ticket.id_customer = customer_id
        mock_ticket.id_employee = uuid4()
        
        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        service.message_repo = mock_repo
        
        # Should not raise
        result = service.validate_participant(ticket_id, customer_id)
        assert result is True

    def test_validate_participant_allows_assigned_employee(self):
        """Test validate_participant allows employee assigned to ticket"""
        db = MagicMock()
        service = ChatService(db)
        
        ticket_id = uuid4()
        employee_id = uuid4()
        customer_id = uuid4()
        
        mock_ticket = MagicMock()
        mock_ticket.id_customer = customer_id
        mock_ticket.id_employee = employee_id
        
        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        service.message_repo = mock_repo
        
        # Should not raise
        result = service.validate_participant(ticket_id, employee_id)
        assert result is True

    def test_validate_participant_rejects_unauthorized_user(self):
        """Test validate_participant rejects user not part of ticket"""
        db = MagicMock()
        service = ChatService(db)
        
        ticket_id = uuid4()
        unauthorized_id = uuid4()
        
        mock_ticket = MagicMock()
        mock_ticket.id_customer = uuid4()
        mock_ticket.id_employee = uuid4()
        
        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        service.message_repo = mock_repo
        
        with pytest.raises(HTTPException) as exc_info:
            service.validate_participant(ticket_id, unauthorized_id)
        
        assert exc_info.value.status_code == 403

    def test_validate_participant_raises_404_for_nonexistent_ticket(self):
        """Test validate_participant raises 404 when ticket doesn't exist"""
        db = MagicMock()
        service = ChatService(db)
        
        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = None
        service.message_repo = mock_repo
        
        with pytest.raises(HTTPException) as exc_info:
            service.validate_participant(uuid4(), uuid4())
        
        assert exc_info.value.status_code == 404