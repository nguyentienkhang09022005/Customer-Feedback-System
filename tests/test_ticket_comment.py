"""
Unit tests for Ticket Comment Service.

Tests cover:
- Comment creation (public and internal)
- Comment retrieval with authorization
- Comment update by author only
- Comment deletion by author or admin
- Internal comments (employee-only)
- Notifications on new comments
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from app.services.ticketCommentService import TicketCommentService
from app.schemas.ticketCommentSchema import CommentCreate, CommentUpdate
from app.models.ticketComment import TicketComment

pytestmark = [pytest.mark.unit]


# ============================================================================
# Comment Creation Tests
# ============================================================================

class TestCommentCreation:
    """Tests for ticket comment creation."""

    def test_create_public_comment_customer(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test customer creating public comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(
            content="This is a test comment from customer",
            is_internal=False
        )

        comment = service.create_comment(
            ticket_id=sample_ticket.id_ticket,
            data=data,
            author_id=sample_customer.id,
            author_type="customer"
        )

        assert comment is not None
        assert comment.content == "This is a test comment from customer"
        assert comment.is_internal is False

    def test_create_internal_comment_employee(
        self,
        db_session,
        sample_ticket,
        sample_employee,
        mock_notification_service
    ):
        """Test employee creating internal comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(
            content="Internal note for the team",
            is_internal=True
        )

        comment = service.create_comment(
            ticket_id=sample_ticket.id_ticket,
            data=data,
            author_id=sample_employee.id,
            author_type="employee"
        )

        assert comment is not None
        assert comment.is_internal is True

    def test_create_internal_comment_customer_fails(
        self,
        db_session,
        sample_ticket,
        sample_customer
    ):
        """Test customer cannot create internal comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(
            content="Trying internal comment",
            is_internal=True
        )

        with pytest.raises(Exception) as exc_info:
            service.create_comment(
                ticket_id=sample_ticket.id_ticket,
                data=data,
                author_id=sample_customer.id,
                author_type="customer"
            )

        assert "nội bộ" in str(exc_info.value)

    def test_create_comment_ticket_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test comment creation fails for nonexistent ticket."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="Test")

        with pytest.raises(Exception) as exc_info:
            service.create_comment(
                ticket_id=uuid4(),
                data=data,
                author_id=sample_customer.id,
                author_type="customer"
            )

        assert "Không tìm thấy ticket" in str(exc_info.value)


# ============================================================================
# Comment Retrieval Tests
# ============================================================================

class TestCommentRetrieval:
    """Tests for comment retrieval."""

    def test_get_comments_employee_sees_all(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test employee sees both internal and public comments."""
        service = TicketCommentService(db_session)

        # Create public comment
        public_data = CommentCreate(content="Public comment", is_internal=False)
        service.create_comment(
            sample_ticket.id_ticket, public_data,
            sample_customer.id, "customer"
        )

        # Create internal comment
        internal_data = CommentCreate(content="Internal note", is_internal=True)
        service.create_comment(
            sample_ticket.id_ticket, internal_data,
            sample_employee.id, "employee"
        )

        comments = service.get_comments(sample_ticket.id_ticket, is_employee=True)

        assert len(comments) == 2

    def test_get_comments_customer_sees_only_public(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test customer sees only public comments."""
        service = TicketCommentService(db_session)

        # Create public comment
        public_data = CommentCreate(content="Public comment", is_internal=False)
        service.create_comment(
            sample_ticket.id_ticket, public_data,
            sample_customer.id, "customer"
        )

        # Create internal comment
        internal_data = CommentCreate(content="Internal note", is_internal=True)
        service.create_comment(
            sample_ticket.id_ticket, internal_data,
            sample_employee.id, "employee"
        )

        comments = service.get_comments(sample_ticket.id_ticket, is_employee=False)

        # Customer should only see 1 (public) comment
        assert len(comments) == 1
        assert comments[0].is_internal is False

    def test_get_comments_ticket_not_found(
        self,
        db_session
    ):
        """Test retrieval fails for nonexistent ticket."""
        service = TicketCommentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_comments(uuid4())

        assert "Không tìm thấy ticket" in str(exc_info.value)


# ============================================================================
# Comment Update Tests
# ============================================================================

class TestCommentUpdate:
    """Tests for comment updates."""

    def test_update_comment_by_author(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test author can update their own comment."""
        service = TicketCommentService(db_session)

        # Create comment
        data = CommentCreate(content="Original content", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        # Update comment
        update_data = CommentUpdate(content="Updated content")
        updated = service.update_comment(
            comment.id_comment,
            update_data,
            sample_customer.id
        )

        assert updated.content == "Updated content"

    def test_update_comment_by_non_author_fails(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test non-author cannot update comment."""
        service = TicketCommentService(db_session)

        # Create comment as customer
        data = CommentCreate(content="Original", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        # Try to update as employee (non-author)
        update_data = CommentUpdate(content="Hijacked")

        with pytest.raises(Exception) as exc_info:
            service.update_comment(
                comment.id_comment,
                update_data,
                sample_employee.id  # Different user
            )

        assert "không có quyền sửa" in str(exc_info.value)


# ============================================================================
# Comment Deletion Tests
# ============================================================================

class TestCommentDeletion:
    """Tests for comment deletion."""

    def test_delete_comment_by_author(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test author can delete their own comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="To be deleted", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        service.delete_comment(comment.id_comment, sample_customer.id)

        # Verify deletion - repo.get_by_id returns None after hard delete
        result = service.repo.get_by_id(comment.id_comment)
        assert result is None

    def test_delete_comment_by_admin(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test admin can delete any comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="Admin delete test", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        # Admin delete (is_admin=True)
        service.delete_comment(comment.id_comment, sample_employee.id, is_admin=True)

        # Verify deletion - repo.get_by_id returns None after hard delete
        result = service.repo.get_by_id(comment.id_comment)
        assert result is None

    def test_delete_comment_by_non_author_non_admin_fails(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test non-author non-admin cannot delete comment."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="Cannot delete", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        # Another employee (not author, not admin) tries to delete
        with pytest.raises(Exception) as exc_info:
            service.delete_comment(
                comment.id_comment,
                sample_employee.id,
                is_admin=False
            )

        assert "không có quyền xóa" in str(exc_info.value)


# ============================================================================
# Edge Cases
# ============================================================================

class TestCommentEdgeCases:
    """Edge case tests for comment service."""

    def test_very_long_comment_content(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test very long comment content."""
        service = TicketCommentService(db_session)

        long_content = "A" * 10000

        data = CommentCreate(content=long_content, is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        assert len(comment.content) == 10000

    def test_special_characters_in_comment(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test special characters in comment."""
        service = TicketCommentService(db_session)

        special_content = "Hello! 🐱 @user #topic with <html> & symbols"

        data = CommentCreate(content=special_content, is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        assert comment.content == special_content

    def test_empty_comment_content(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test empty comment content."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        assert comment.content == ""

    def test_update_empty_content_keeps_old_content(
        self,
        db_session,
        sample_ticket,
        sample_customer,
        mock_notification_service
    ):
        """Test updating with empty content keeps old content."""
        service = TicketCommentService(db_session)

        data = CommentCreate(content="Original content", is_internal=False)
        comment = service.create_comment(
            sample_ticket.id_ticket, data,
            sample_customer.id, "customer"
        )

        update_data = CommentUpdate(content="")
        updated = service.update_comment(
            comment.id_comment,
            update_data,
            sample_customer.id
        )

        # Content should remain unchanged when empty update
        assert updated.content == "Original content"