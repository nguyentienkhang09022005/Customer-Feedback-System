import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from app.services.chatService import ChatService
from app.schemas.chatSchema import MessageCreate, MessageType


class TestChatService:
    def test_send_message_creates_message_in_db(self):
        db = MagicMock()
        ticket_id = uuid4()
        sender_id = uuid4()
        content = "Hello, how can I help?"

        mock_ticket = MagicMock()
        mock_ticket.id_customer = sender_id
        mock_ticket.id_employee = uuid4()

        mock_sender = MagicMock()
        mock_sender.id = sender_id
        mock_sender.first_name = "John"
        mock_sender.last_name = "Doe"
        mock_sender.avatar = None

        mock_message = MagicMock()
        mock_message.id_message = uuid4()
        mock_message.message = content
        mock_message.id_ticket = ticket_id
        mock_message.id_sender = sender_id
        mock_message.message_type = "text"
        mock_message.is_read = False
        mock_message.created_at = datetime.now(timezone.utc)

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        mock_repo.create_message.return_value = mock_message

        db.query.return_value.filter.return_value.first.return_value = mock_sender

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        result = service.send_message(ticket_id, sender_id, content)

        mock_repo.create_message.assert_called_once()
        assert result.content == content

    def test_send_message_with_image_type(self):
        db = MagicMock()
        ticket_id = uuid4()
        sender_id = uuid4()
        content = "https://cloudinary.com/image.jpg"
        message_type = MessageType.IMAGE

        mock_ticket = MagicMock()
        mock_ticket.id_customer = uuid4()
        mock_ticket.id_employee = sender_id

        mock_sender = MagicMock()
        mock_sender.id = sender_id
        mock_sender.first_name = "Jane"
        mock_sender.last_name = "Smith"
        mock_sender.avatar = None

        mock_message = MagicMock()
        mock_message.id_message = uuid4()
        mock_message.message = content
        mock_message.id_ticket = ticket_id
        mock_message.id_sender = sender_id
        mock_message.message_type = "image"
        mock_message.is_read = False
        mock_message.created_at = datetime.now(timezone.utc)

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        mock_repo.create_message.return_value = mock_message

        db.query.return_value.filter.return_value.first.return_value = mock_sender

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        result = service.send_message(ticket_id, sender_id, content, message_type)

        mock_repo.create_message.assert_called_once()
        assert result.content == content
        assert result.message_type.value == "image"

    def test_get_chat_history_returns_paginated_messages(self):
        db = MagicMock()
        ticket_id = uuid4()
        page = 1
        limit = 20

        sender_id = uuid4()
        mock_sender = MagicMock()
        mock_sender.id = sender_id
        mock_sender.first_name = "John"
        mock_sender.last_name = "Doe"
        mock_sender.avatar = None

        mock_messages = [
            MagicMock(
                id_message=uuid4(),
                message="Message 1",
                message_type="text",
                is_read=False,
                created_at=datetime.now(timezone.utc),
                id_sender=sender_id
            ),
            MagicMock(
                id_message=uuid4(),
                message="Message 2",
                message_type="text",
                is_read=True,
                created_at=datetime.now(timezone.utc),
                id_sender=sender_id
            )
        ]

        mock_repo = MagicMock()
        mock_repo.get_messages_by_ticket.return_value = (mock_messages, 2)

        db.query.return_value.filter.return_value.first.return_value = mock_sender

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        messages, total = service.get_chat_history(ticket_id, page, limit)

        assert len(messages) == 2
        assert total == 2
        mock_repo.get_messages_by_ticket.assert_called_once_with(ticket_id, page, limit)

    def test_validate_participant_returns_true_for_customer(self):
        db = MagicMock()
        ticket_id = uuid4()
        customer_id = uuid4()

        mock_ticket = MagicMock()
        mock_ticket.id_customer = customer_id
        mock_ticket.id_employee = uuid4()

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        result = service.validate_participant(ticket_id, customer_id)

        assert result is True

    def test_validate_participant_returns_true_for_employee(self):
        db = MagicMock()
        ticket_id = uuid4()
        employee_id = uuid4()

        mock_ticket = MagicMock()
        mock_ticket.id_customer = uuid4()
        mock_ticket.id_employee = employee_id

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        result = service.validate_participant(ticket_id, employee_id)

        assert result is True

    def test_validate_participant_returns_false_for_stranger(self):
        db = MagicMock()
        ticket_id = uuid4()
        stranger_id = uuid4()

        mock_ticket = MagicMock()
        mock_ticket.id_customer = uuid4()
        mock_ticket.id_employee = uuid4()

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            service.validate_participant(ticket_id, stranger_id)

        assert exc_info.value.status_code == 403

    def test_validate_participant_raises_when_ticket_not_found(self):
        db = MagicMock()
        ticket_id = uuid4()
        user_id = uuid4()

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = None

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            service.validate_participant(ticket_id, user_id)

        assert exc_info.value.status_code == 404
        assert "Ticket không tồn tại" in str(exc_info.value.detail)

    def test_mark_messages_as_read(self):
        db = MagicMock()
        ticket_id = uuid4()
        user_id = uuid4()

        mock_ticket = MagicMock()
        mock_ticket.id_customer = user_id
        mock_ticket.id_employee = uuid4()

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        service.mark_messages_read(ticket_id, user_id)

        mock_repo.mark_as_read.assert_called_once_with(ticket_id, user_id)

    def test_get_unread_count(self):
        db = MagicMock()
        ticket_id = uuid4()
        user_id = uuid4()

        mock_ticket = MagicMock()
        mock_ticket.id_customer = uuid4()
        mock_ticket.id_employee = user_id

        mock_repo = MagicMock()
        mock_repo.get_ticket_by_id.return_value = mock_ticket
        mock_repo.get_unread_count.return_value = 5

        service = ChatService.__new__(ChatService)
        service.db = db
        service.message_repo = mock_repo

        result = service.get_unread_count(ticket_id, user_id)

        assert result == 5
        mock_repo.get_unread_count.assert_called_once_with(ticket_id, user_id)