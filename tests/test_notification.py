"""
Unit tests for Notification Service.

Tests cover:
- Notification creation
- Get notifications (all, unread only)
- Mark notification as read
- Permission checks
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import uuid

from app.services.notificationService import NotificationService
from app.schemas.notificationSchema import NotificationCreate
from app.models.interaction import Notification


# ============================================================================
# Notification Creation Tests
# ============================================================================

class TestNotificationCreation:
    """Tests for notification creation."""

    def test_create_and_send_basic(
        self,
        db_session,
        sample_customer
    ):
        """Test creating basic notification."""
        service = NotificationService(db_session)

        data = NotificationCreate(
            title="Test Notification",
            content="Test content",
            notification_type="TEST",
            id_receiver=sample_customer.id
        )

        notification = service.create_and_send(data)

        assert notification is not None
        assert notification.title == "Test Notification"
        assert notification.content == "Test content"
        assert notification.notification_type == "TEST"
        assert notification.id_receiver == sample_customer.id

    def test_create_with_reference(
        self,
        db_session,
        sample_customer,
        sample_ticket
    ):
        """Test creating notification with ticket reference."""
        service = NotificationService(db_session)

        data = NotificationCreate(
            title="Ticket Update",
            content="Your ticket was updated",
            notification_type="TICKET_UPDATE",
            id_reference=sample_ticket.id_ticket,
            id_receiver=sample_customer.id
        )

        notification = service.create_and_send(data)

        assert notification.id_reference == sample_ticket.id_ticket

    def test_create_without_content(
        self,
        db_session,
        sample_customer
    ):
        """Test creating notification without content."""
        service = NotificationService(db_session)

        data = NotificationCreate(
            title="Silent notification",
            id_receiver=sample_customer.id
        )

        notification = service.create_and_send(data)

        assert notification.content is None


# ============================================================================
# Notification Retrieval Tests
# ============================================================================

class TestNotificationRetrieval:
    """Tests for notification retrieval."""

    def test_get_my_notifications(
        self,
        db_session,
        sample_customer
    ):
        """Test getting all notifications for user."""
        service = NotificationService(db_session)

        # Create notifications
        for i in range(3):
            data = NotificationCreate(
                title=f"Notification {i}",
                content=f"Content {i}",
                notification_type="TEST",
                id_receiver=sample_customer.id
            )
            service.create_and_send(data)

        notifications = service.get_my_notifications(sample_customer.id)

        assert len(notifications) == 3

    def test_get_unread_notifications(
        self,
        db_session,
        sample_customer
    ):
        """Test getting only unread notifications."""
        service = NotificationService(db_session)

        # Create notifications
        for i in range(3):
            data = NotificationCreate(
                title=f"Unread {i}",
                content=f"Content {i}",
                notification_type="TEST",
                id_receiver=sample_customer.id
            )
            service.create_and_send(data)

        # Mark one as read
        notifications = service.get_my_notifications(sample_customer.id)
        if notifications:
            service.mark_as_read(notifications[0].id_notification, sample_customer.id)

        unread = service.get_my_notifications(sample_customer.id, is_unread_only=True)

        assert len(unread) == 2

    def test_get_notifications_pagination(
        self,
        db_session,
        sample_customer
    ):
        """Test notification pagination."""
        service = NotificationService(db_session)

        # Create 5 notifications
        for i in range(5):
            data = NotificationCreate(
                title=f"Page {i}",
                content=f"Content {i}",
                notification_type="TEST",
                id_receiver=sample_customer.id
            )
            service.create_and_send(data)

        # Get with pagination
        page1 = service.get_my_notifications(sample_customer.id, skip=0, limit=2)
        page2 = service.get_my_notifications(sample_customer.id, skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2

    def test_get_notifications_empty(
        self,
        db_session,
        sample_customer
    ):
        """Test getting notifications when none exist."""
        service = NotificationService(db_session)

        notifications = service.get_my_notifications(sample_customer.id)

        assert len(notifications) == 0


# ============================================================================
# Mark as Read Tests
# ============================================================================

class TestMarkAsRead:
    """Tests for marking notifications as read."""

    def test_mark_as_read_success(
        self,
        db_session,
        sample_customer
    ):
        """Test marking notification as read."""
        service = NotificationService(db_session)

        # Create notification
        data = NotificationCreate(
            title="To read",
            content="Content",
            notification_type="TEST",
            id_receiver=sample_customer.id
        )
        notification = service.create_and_send(data)

        assert notification.is_read is False

        # Mark as read
        updated = service.mark_as_read(notification.id_notification, sample_customer.id)

        assert updated.is_read is True

    def test_mark_as_read_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test marking nonexistent notification as read."""
        service = NotificationService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.mark_as_read(uuid4(), sample_customer.id)

        assert "Không tìm thấy" in str(exc_info.value)

    def test_mark_as_read_wrong_user(
        self,
        db_session,
        sample_customer,
        sample_employee
    ):
        """Test marking notification owned by another user fails."""
        service = NotificationService(db_session)

        # Create notification for customer
        data = NotificationCreate(
            title="Customer only",
            content="Content",
            notification_type="TEST",
            id_receiver=sample_customer.id
        )
        notification = service.create_and_send(data)

        # Employee tries to mark as read
        with pytest.raises(Exception) as exc_info:
            service.mark_as_read(notification.id_notification, sample_employee.id)

        assert "không có quyền" in str(exc_info.value)


# ============================================================================
# Notification Types Tests
# ============================================================================

class TestNotificationTypes:
    """Tests for different notification types."""

    def test_ticket_notification_types(
        self,
        db_session,
        sample_customer,
        sample_employee
    ):
        """Test various ticket notification types."""
        service = NotificationService(db_session)

        types = [
            "TICKET_CREATED",
            "TICKET_ASSIGNED",
            "TICKET_UPDATED",
            "TICKET_RESOLVED",
            "TICKET_REOPENED"
        ]

        for notif_type in types:
            data = NotificationCreate(
                title=f"Ticket {notif_type}",
                content=f"Ticket was {notif_type.lower()}",
                notification_type=notif_type,
                id_receiver=sample_customer.id
            )
            notification = service.create_and_send(data)
            assert notification.notification_type == notif_type

    def test_appointment_notification_types(
        self,
        db_session,
        sample_customer
    ):
        """Test appointment notification types."""
        service = NotificationService(db_session)

        types = [
            "APPOINTMENT_REQUEST",
            "APPOINTMENT_ACCEPTED",
            "APPOINTMENT_REJECTED",
            "APPOINTMENT_CANCELLED"
        ]

        for notif_type in types:
            data = NotificationCreate(
                title=f"Appointment {notif_type}",
                content=f"Appointment was {notif_type.lower()}",
                notification_type=notif_type,
                id_receiver=sample_customer.id
            )
            notification = service.create_and_send(data)
            assert notification.notification_type == notif_type

    def test_other_notification_types(
        self,
        db_session,
        sample_customer
    ):
        """Test other notification types."""
        service = NotificationService(db_session)

        types = [
            "NEW_COMMENT",
            "EVALUATE",
            "CSAT_SURVEY",
            "SLA_ESCALATED"
        ]

        for notif_type in types:
            data = NotificationCreate(
                title=f"Notif {notif_type}",
                content=f"Content for {notif_type}",
                notification_type=notif_type,
                id_receiver=sample_customer.id
            )
            notification = service.create_and_send(data)
            assert notification.notification_type == notif_type


# ============================================================================
# Edge Cases
# ============================================================================

class TestNotificationEdgeCases:
    """Edge case tests for notification service."""

    def test_very_long_content(
        self,
        db_session,
        sample_customer
    ):
        """Test notification with very long content."""
        service = NotificationService(db_session)

        long_content = "A" * 1000
        data = NotificationCreate(
            title="Long content",
            content=long_content,
            notification_type="TEST",
            id_receiver=sample_customer.id
        )

        notification = service.create_and_send(data)
        assert len(notification.content) == 1000

    def test_unicode_content(
        self,
        db_session,
        sample_customer
    ):
        """Test notification with unicode characters."""
        service = NotificationService(db_session)

        data = NotificationCreate(
            title="Thông báo tiếng Việt",
            content="Nội dung thông báo có dấu",
            notification_type="TEST",
            id_receiver=sample_customer.id
        )

        notification = service.create_and_send(data)
        assert notification.title == "Thông báo tiếng Việt"

    def test_multiple_recipients(
        self,
        db_session,
        sample_customer,
        sample_employee
    ):
        """Test sending to multiple recipients."""
        service = NotificationService(db_session)

        for recipient in [sample_customer.id, sample_employee.id]:
            data = NotificationCreate(
                title="Multi recipient",
                content="Sent to multiple",
                notification_type="TEST",
                id_receiver=recipient
            )
            notification = service.create_and_send(data)
            assert notification.id_receiver == recipient