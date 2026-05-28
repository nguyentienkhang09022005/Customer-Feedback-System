"""
Unit tests for Audit Log Service.

Tests cover:
- Logging actions
- Retrieving logs for entity
- Paginated log retrieval
- CSV export
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import uuid
import json

from app.services.auditLogService import AuditLogService
from app.schemas.auditLogSchema import AuditLogCreate
from app.models.system import AuditLog

pytestmark = [pytest.mark.unit]


# ============================================================================
# Audit Log Creation Tests
# ============================================================================

class TestAuditLogCreation:
    """Tests for audit log creation."""

    def test_log_action_success(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test successful action logging."""
        service = AuditLogService(db_session)

        old_data = {"status": "New"}
        new_data = {"status": "In Progress"}

        log = service.log_action(
            log_type="ticket",
            action="status_changed",
            old_data=old_data,
            new_data=new_data,
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        assert log is not None
        assert log.action == "status_changed"
        assert log.id_employee == sample_employee.id_employee

    def test_log_action_without_old_data(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test logging action without old data (creation)."""
        service = AuditLogService(db_session)

        new_data = {"title": "New Ticket", "status": "New"}

        log = service.log_action(
            log_type="ticket",
            action="created",
            old_data=None,
            new_data=new_data,
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        assert log.old_value is None
        assert log.new_value is not None

    def test_log_action_without_new_data(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test logging action without new data (deletion)."""
        service = AuditLogService(db_session)

        old_data = {"title": "Deleted Ticket", "status": "Deleted"}

        log = service.log_action(
            log_type="ticket",
            action="deleted",
            old_data=old_data,
            new_data=None,
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        assert log.old_value is not None
        assert log.new_value is None

    def test_log_action_with_complex_data(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test logging with complex nested data."""
        service = AuditLogService(db_session)

        complex_data = {
            "user": {"name": "John", "roles": ["admin", "user"]},
            "changes": ["field1", "field2"]
        }

        log = service.log_action(
            log_type="user",
            action="permissions_updated",
            old_data=None,
            new_data=complex_data,
            id_reference=sample_employee.id,
            id_employee=sample_employee.id_employee
        )

        assert log is not None
        parsed = json.loads(log.new_value)
        assert parsed["user"]["name"] == "John"


# ============================================================================
# Audit Log Retrieval Tests
# ============================================================================

class TestAuditLogRetrieval:
    """Tests for audit log retrieval."""

    def test_get_logs_for_entity(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test getting all logs for a specific entity."""
        service = AuditLogService(db_session)

        # Create multiple log entries
        for i in range(3):
            service.log_action(
                log_type="ticket",
                action=f"action_{i}",
                old_data={"index": i},
                new_data={"index": i + 1},
                id_reference=sample_ticket.id_ticket,
                id_employee=sample_employee.id_employee
            )

        logs = service.get_logs_for_entity(sample_ticket.id_ticket)

        assert len(logs) >= 3

    def test_get_all_logs_paginated(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test getting all logs with pagination."""
        service = AuditLogService(db_session)

        # Create 5 logs
        for i in range(5):
            service.log_action(
                log_type="ticket",
                action=f"paginated_{i}",
                old_data=None,
                new_data={"index": i},
                id_reference=sample_ticket.id_ticket,
                id_employee=sample_employee.id_employee
            )

        page1, total = service.get_all_logs(page=1, limit=2)

        assert len(page1) == 2
        assert total >= 5

    def test_get_logs_filtered_by_type(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test getting logs filtered by log type."""
        service = AuditLogService(db_session)

        # Create ticket logs
        service.log_action(
            log_type="ticket",
            action="ticket_action",
            old_data=None,
            new_data={"type": "ticket"},
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        # Create user logs
        service.log_action(
            log_type="user",
            action="user_action",
            old_data=None,
            new_data={"type": "user"},
            id_reference=sample_employee.id,
            id_employee=sample_employee.id_employee
        )

        # Filter by ticket type
        ticket_logs, total = service.get_all_logs(log_type="ticket")

        assert all(log.log_type == "ticket" for log in ticket_logs)

    def test_get_logs_no_filter(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test getting logs without filter returns all types."""
        service = AuditLogService(db_session)

        service.log_action(
            log_type="ticket",
            action="ticket_log",
            old_data=None,
            new_data={"log": "ticket"},
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        service.log_action(
            log_type="user",
            action="user_log",
            old_data=None,
            new_data={"log": "user"},
            id_reference=sample_employee.id,
            id_employee=sample_employee.id_employee
        )

        all_logs, total = service.get_all_logs()

        assert total >= 2


# ============================================================================
# Audit Log Export Tests
# ============================================================================

class TestAuditLogExport:
    """Tests for audit log CSV export."""

    def test_export_to_csv(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test exporting logs to CSV format."""
        service = AuditLogService(db_session)

        # Create log
        service.log_action(
            log_type="ticket",
            action="status_changed",
            old_data={"status": "New"},
            new_data={"status": "In Progress"},
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        csv_data = service.export_to_csv()

        assert len(csv_data) >= 1
        assert "action" in csv_data[0]
        assert "entity_type" in csv_data[0]

    def test_export_to_csv_filtered(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test exporting logs filtered by type."""
        service = AuditLogService(db_session)

        service.log_action(
            log_type="ticket",
            action="ticket_only",
            old_data=None,
            new_data={"type": "ticket"},
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        csv_data = service.export_to_csv(log_type="ticket")

        assert all(row["entity_type"] == "ticket" for row in csv_data)

    def test_export_to_csv_empty(self, db_session):
        """Test exporting when no logs exist."""
        service = AuditLogService(db_session)

        csv_data = service.export_to_csv()

        assert isinstance(csv_data, list)


# ============================================================================
# Edge Cases
# ============================================================================

class TestAuditLogEdgeCases:
    """Edge case tests for audit log service."""

    def test_log_action_unicode_data(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test logging action with unicode data."""
        service = AuditLogService(db_session)

        unicode_data = {
            "name": "Nguyễn Văn Minh",
            "department": "Phòng Kỹ thuật"
        }

        log = service.log_action(
            log_type="user",
            action="unicode_test",
            old_data=None,
            new_data=unicode_data,
            id_reference=sample_employee.id,
            id_employee=sample_employee.id_employee
        )

        assert log is not None

    def test_log_action_empty_data(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test logging action with empty data."""
        service = AuditLogService(db_session)

        log = service.log_action(
            log_type="ticket",
            action="empty_test",
            old_data={},
            new_data={},
            id_reference=sample_ticket.id_ticket,
            id_employee=sample_employee.id_employee
        )

        assert log is not None

    def test_get_logs_pagination_page2(
        self,
        db_session,
        sample_employee,
        sample_ticket
    ):
        """Test getting second page of logs."""
        service = AuditLogService(db_session)

        # Create 5 logs
        for i in range(5):
            service.log_action(
                log_type="ticket",
                action=f"page2_{i}",
                old_data=None,
                new_data={"index": i},
                id_reference=sample_ticket.id_ticket,
                id_employee=sample_employee.id_employee
            )

        # Get second page
        page2, total = service.get_all_logs(page=2, limit=2)

        assert len(page2) == min(2, total - 2)

    def test_get_logs_nonexistent_type(
        self,
        db_session
    ):
        """Test getting logs with nonexistent type returns empty."""
        service = AuditLogService(db_session)

        logs, total = service.get_all_logs(log_type="nonexistent_type")

        assert len(logs) == 0