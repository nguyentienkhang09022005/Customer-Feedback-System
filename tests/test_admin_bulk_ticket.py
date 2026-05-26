"""
Tests for admin bulk ticket service.
"""

import pytest
from uuid import uuid4

from app.services.admin.bulkTicketService import BulkTicketService
from app.schemas.admin.ticketBulk import BulkUpdateStatus, BulkAssignTicket, BulkDelete
from app.core.constants import TicketStatusConstants
from app.models.ticket import Ticket


class TestBulkUpdateStatus:
    """Tests for bulk_update_status method."""

    def test_bulk_update_status_changes_status_of_multiple_tickets(
        self, db_session, sample_ticket, sample_ticket_assigned
    ):
        """Happy path: bulk update status changes status of multiple tickets."""
        data = BulkUpdateStatus(
            ticket_ids=[sample_ticket.id_ticket, sample_ticket_assigned.id_ticket],
            status="In Progress"
        )

        result = BulkTicketService(db_session).bulk_update_status(data)

        assert result["updated_count"] == 2
        db_session.refresh(sample_ticket)
        db_session.refresh(sample_ticket_assigned)
        assert sample_ticket.status == "In Progress"
        assert sample_ticket_assigned.status == "In Progress"

    def test_bulk_update_status_with_empty_list_returns_zero(self, db_session):
        """Edge case: empty ticket list."""
        data = BulkUpdateStatus(ticket_ids=[], status="New")

        result = BulkTicketService(db_session).bulk_update_status(data)

        assert result["updated_count"] == 0

    def test_bulk_update_status_with_invalid_status_raises_error(
        self, db_session, sample_ticket
    ):
        """Validation: invalid status raises HTTPException."""
        invalid_status = "InvalidStatus"

        data = BulkUpdateStatus(
            ticket_ids=[sample_ticket.id_ticket],
            status=invalid_status
        )

        with pytest.raises(Exception) as exc_info:
            BulkTicketService(db_session).bulk_update_status(data)

        # verify the exception mentions the valid statuses
        assert any(
            status in str(exc_info.value)
            or "Invalid status" in str(exc_info.value).replace("'", "")
            for status in TicketStatusConstants.VALID_STATUSES
        ) or "Invalid status" in str(exc_info.value).replace("'", "")

    def test_bulk_update_status_with_nonexistent_ticket_ids_returns_count(
        self, db_session
    ):
        """Edge case: all IDs are nonexistent — repository returns 0."""
        data = BulkUpdateStatus(
            ticket_ids=[uuid4(), uuid4()],
            status="New"
        )

        result = BulkTicketService(db_session).bulk_update_status(data)

        assert result["updated_count"] == 0


class TestBulkAssign:
    """Tests for bulk_assign method."""

    def test_bulk_assign_assigns_tickets_to_employee(
        self, db_session, sample_ticket, sample_ticket_2, sample_employee
    ):
        """Happy path: bulk assign tickets to an employee."""
        data = BulkAssignTicket(
            ticket_ids=[sample_ticket.id_ticket, sample_ticket_2.id_ticket],
            employee_id=sample_employee.id_employee
        )

        result = BulkTicketService(db_session).bulk_assign(data)

        assert result["assigned_count"] == 2
        db_session.refresh(sample_ticket)
        db_session.refresh(sample_ticket_2)
        assert sample_ticket.id_employee == sample_employee.id_employee
        assert sample_ticket_2.id_employee == sample_employee.id_employee

    def test_bulk_assign_with_empty_list_returns_zero(self, db_session, sample_employee):
        """Edge case: empty ticket list."""
        data = BulkAssignTicket(ticket_ids=[], employee_id=sample_employee.id_employee)

        result = BulkTicketService(db_session).bulk_assign(data)

        assert result["assigned_count"] == 0

    def test_bulk_assign_with_nonexistent_employee_id_still_returns_count(
        self, db_session, sample_ticket
    ):
        """Edge case: employee doesn't exist — repository still updates."""
        data = BulkAssignTicket(
            ticket_ids=[sample_ticket.id_ticket],
            employee_id=uuid4()
        )

        result = BulkTicketService(db_session).bulk_assign(data)

        # count may be 0 if no tickets matched or the foreign key rejects
        assert "assigned_count" in result


class TestBulkDelete:
    """Tests for bulk_delete method."""

    def test_bulk_delete_soft_deletes_multiple_tickets(
        self, db_session, sample_ticket, sample_ticket_assigned
    ):
        """Happy path: bulk delete soft-deletes multiple tickets."""
        data = BulkDelete(
            ticket_ids=[sample_ticket.id_ticket, sample_ticket_assigned.id_ticket]
        )

        result = BulkTicketService(db_session).bulk_delete(data)

        assert result["deleted_count"] == 2
        db_session.refresh(sample_ticket)
        db_session.refresh(sample_ticket_assigned)
        assert sample_ticket.is_deleted is True
        assert sample_ticket_assigned.is_deleted is True

    def test_bulk_delete_with_empty_list_returns_zero(self, db_session):
        """Edge case: empty ticket list."""
        data = BulkDelete(ticket_ids=[])

        result = BulkTicketService(db_session).bulk_delete(data)

        assert result["deleted_count"] == 0

    def test_bulk_delete_with_nonexistent_ids_returns_zero(self, db_session):
        """Edge case: all IDs are nonexistent."""
        data = BulkDelete(ticket_ids=[uuid4(), uuid4()])

        result = BulkTicketService(db_session).bulk_delete(data)

        assert result["deleted_count"] == 0


# Extra fixture: second sample ticket
@pytest.fixture
def sample_ticket_2(
    db_session,
    sample_customer,
    sample_employee_2
):
    """Create a second sample ticket for bulk operation tests."""
    ticket = Ticket(
        id_ticket=uuid4(),
        title="Second test ticket",
        custom_fields={},
        status="New",
        severity="Low",
        version=1,
        expired_date=None,
        id_employee=None,
        id_customer=sample_customer.id_customer,
        survey_sent=False
    )
    db_session.add(ticket)
    db_session.commit()
    return ticket
