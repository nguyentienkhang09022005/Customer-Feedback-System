"""
Unit tests for Escalation Service.

Tests cover:
- Escalate ticket to manager
- Escalate ticket to level 2
- Auto-escalate overdue tickets
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import uuid
from datetime import datetime, timedelta

from app.services.escalationService import EscalationService
from app.schemas.notificationSchema import NotificationCreate
from app.models.ticket import Ticket


# ============================================================================
# Escalation to Manager Tests
# ============================================================================

class TestEscalateToManager:
    """Tests for escalating tickets to department manager."""

    def test_escalate_to_manager_success(
        self,
        db_session,
        sample_ticket,
        sample_manager,
        sample_ticket_category,
        sample_department
    ):
        """Test successful escalation to manager."""
        # Setup: ticket needs category with department that has manager
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.id_employee = None  # Unassigned
        sample_ticket_category.id_department = sample_department.id_department

        # Setup manager in same department
        sample_manager.id_department = sample_department.id_department
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_manager(sample_ticket, "Urgent issue")

        assert result is True

    def test_escalate_to_manager_no_category(self, db_session, sample_ticket):
        """Test escalation fails when ticket has no category."""
        sample_ticket.id_category = None
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_manager(sample_ticket, "No category")

        assert result is False

    def test_escalate_to_manager_no_manager_in_department(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category,
        sample_department
    ):
        """Test escalation fails when department has no manager."""
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket_category.id_department = sample_department.id_department
        sample_department.manager_id = None
        # Make sure no employee is a manager in this department
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_manager(sample_ticket)

        assert result is False

    def test_escalate_to_manager_already_assigned(
        self,
        db_session,
        sample_ticket,
        sample_employee,
        sample_ticket_category,
        sample_department
    ):
        """Test escalation skipped when manager is already assigned."""
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.id_employee = sample_employee.id_employee  # Assigned
        sample_ticket_category.id_department = sample_department.id_department
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_manager(sample_ticket)

        # Should return False because manager is already assigned
        assert result is False


# ============================================================================
# Escalation to Level 2 Tests
# ============================================================================

class TestEscalateToLevel2:
    """Tests for escalating tickets to level 2 support."""

    def test_escalate_to_level2_with_employee(
        self,
        db_session,
        sample_ticket,
        sample_employee
    ):
        """Test escalation to level 2 when ticket has assigned employee."""
        sample_ticket.id_employee = sample_employee.id_employee
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_level2(sample_ticket)

        assert result is True

    def test_escalate_to_level2_unassigned(self, db_session, sample_ticket):
        """Test escalation to level 2 when no employee assigned."""
        sample_ticket.id_employee = None
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_level2(sample_ticket)

        # Should return True but not send notification
        assert result is True


# ============================================================================
# Auto-Escalate Overdue Tickets Tests
# ============================================================================

class TestAutoEscalateOverdue:
    """Tests for auto-escalation of overdue tickets."""

    def test_auto_escalate_with_overdue_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category,
        sample_department
    ):
        """Test auto-escalation finds overdue tickets."""
        # Setup overdue ticket
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.id_employee = None
        sample_ticket.status = "In Progress"
        sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
        sample_ticket_category.id_department = sample_department.id_department
        db_session.commit()

        service = EscalationService(db_session)

        result = service.auto_escalate_overdue_tickets()

        assert "total_overdue" in result
        assert "escalated" in result
        assert "errors" in result

    def test_auto_escalate_no_overdue_tickets(
        self,
        db_session,
        sample_ticket
    ):
        """Test auto-escalation with no overdue tickets."""
        # Ticket not overdue
        sample_ticket.status = "New"
        sample_ticket.expired_date = datetime.utcnow() + timedelta(days=7)
        db_session.commit()

        service = EscalationService(db_session)

        result = service.auto_escalate_overdue_tickets()

        assert result["total_overdue"] == 0
        assert result["escalated"] == 0

    def test_auto_escalate_ignores_resolved_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category
    ):
        """Test auto-escalation ignores resolved/closed tickets."""
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.status = "Resolved"
        sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        service = EscalationService(db_session)

        result = service.auto_escalate_overdue_tickets()

        # Resolved tickets should not be counted
        assert result["total_overdue"] == 0

    def test_auto_escalate_ignores_closed_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category
    ):
        """Test auto-escalation ignores closed tickets."""
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.status = "Closed"
        sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()

        service = EscalationService(db_session)

        result = service.auto_escalate_overdue_tickets()

        assert result["total_overdue"] == 0

    def test_auto_escalate_multiple_statuses(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category
    ):
        """Test auto-escalation considers ticket status correctly."""
        # Should escalate: New, In Progress, Pending, On Hold
        # Should NOT escalate: Resolved, Closed
        statuses_to_test = ["New", "In Progress", "Pending", "On Hold"]

        for status in statuses_to_test:
            sample_ticket.status = status
            sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
            sample_ticket.id_category = sample_ticket_category.id_category
            db_session.commit()

            service = EscalationService(db_session)
            result = service.auto_escalate_overdue_tickets()

            # All these statuses should be overdue
            assert result["total_overdue"] >= 1, f"Status {status} should be counted"


# ============================================================================
# Edge Cases
# ============================================================================

class TestEscalationEdgeCases:
    """Edge case tests for escalation service."""

    def test_escalate_ticket_with_long_title(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category,
        sample_department,
        sample_manager
    ):
        """Test escalating ticket with very long title."""
        sample_ticket.title = "A" * 100
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.id_employee = None
        sample_ticket_category.id_department = sample_department.id_department
        db_session.commit()

        service = EscalationService(db_session)

        result = service.escalate_to_manager(sample_ticket)

        assert result is True

    def test_escalate_ticket_with_empty_reason(
        self,
        db_session,
        sample_ticket,
        sample_ticket_category,
        sample_department,
        sample_manager
    ):
        """Test escalating without explicit reason."""
        sample_ticket.id_category = sample_ticket_category.id_category
        sample_ticket.id_employee = None
        sample_ticket_category.id_department = sample_department.id_department
        db_session.commit()

        service = EscalationService(db_session)

        # Should work without reason
        result = service.escalate_to_manager(sample_ticket, reason=None)

        assert result is True

    def test_auto_escalate_error_handling(
        self,
        db_session,
        sample_ticket
    ):
        """Test auto-escalation handles errors gracefully."""
        # Make ticket invalid for escalation
        sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
        sample_ticket.status = "New"
        sample_ticket.id_category = None
        db_session.commit()

        service = EscalationService(db_session)

        # Should not raise exception
        result = service.auto_escalate_overdue_tickets()

        assert "errors" in result
        # Errors should be 0 or more (not crash)
        assert result["errors"] >= 0