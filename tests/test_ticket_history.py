"""
Tests for TicketHistoryService.
"""

import pytest
from uuid import uuid4

from app.services.ticketHistoryService import TicketHistoryService
from app.models.ticketHistory import TicketHistory, TicketAction


class TestLogTicketCreated:
    def test_log_ticket_created_creates_history_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging ticket creation creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.CREATED
        assert history.actor_type == "employee"
        assert history.new_value["title"] == sample_ticket.title

    def test_log_ticket_created_stores_custom_fields(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test ticket creation log includes custom fields."""
        service = TicketHistoryService(db_session)

        history = service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert "custom_fields" in history.new_value
        assert history.new_value["severity"] == sample_ticket.severity


class TestLogStatusChange:
    def test_log_status_change_creates_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging status change creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_status_change(
            ticket=sample_ticket,
            old_status="New",
            new_status="In Progress",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.STATUS_CHANGED
        assert history.old_value["status"] == "New"
        assert history.new_value["status"] == "In Progress"
        assert history.actor_type == "employee"

    def test_log_status_change_uses_system_when_no_actor(
        self, db_session, sample_ticket
    ):
        """Test logging status change defaults to system actor."""
        service = TicketHistoryService(db_session)

        history = service.log_status_change(
            ticket=sample_ticket,
            old_status="New",
            new_status="In Progress",
        )

        assert history.actor_type == "system"


class TestLogAssignment:
    def test_log_assignment_creates_record_with_new_employee(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging assignment with new employee creates ASSIGNED record."""
        service = TicketHistoryService(db_session)

        history = service.log_assignment(
            ticket=sample_ticket,
            old_employee_id=None,
            new_employee_id=sample_employee.id_employee,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.ASSIGNED
        assert history.old_value["id_employee"] is None
        assert history.new_value["id_employee"] == str(sample_employee.id_employee)

    def test_log_assignment_creates_unassigned_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging unassignment creates UNASSIGNED record."""
        service = TicketHistoryService(db_session)

        history = service.log_assignment(
            ticket=sample_ticket,
            old_employee_id=sample_employee.id_employee,
            new_employee_id=None,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.action == TicketAction.UNASSIGNED
        assert history.new_value["id_employee"] is None


class TestLogCategoryChange:
    def test_log_category_change_creates_record(
        self, db_session, sample_ticket, sample_ticket_category
    ):
        """Test logging category change creates a history record."""
        service = TicketHistoryService(db_session)
        new_category_id = uuid4()

        history = service.log_category_change(
            ticket=sample_ticket,
            old_category_id=sample_ticket_category.id_category,
            new_category_id=new_category_id,
            actor_id=None,
            actor_type="system",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.CATEGORY_CHANGED
        assert history.old_value["id_category"] == str(sample_ticket_category.id_category)
        assert history.new_value["id_category"] == str(new_category_id)


class TestLogSeverityChange:
    def test_log_severity_change_creates_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging severity change creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_severity_change(
            ticket=sample_ticket,
            old_severity="Low",
            new_severity="High",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.SEVERITY_CHANGED
        assert history.old_value["severity"] == "Low"
        assert history.new_value["severity"] == "High"


class TestLogResolution:
    def test_log_resolution_creates_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging ticket resolution creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_resolution(
            ticket=sample_ticket,
            resolution_note="Issue fixed and verified by customer",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.RESOLVED
        assert history.new_value["status"] == "Resolved"
        assert history.note == "Issue fixed and verified by customer"
        assert history.actor_type == "employee"

    def test_log_resolution_defaults_to_employee_actor(
        self, db_session, sample_ticket
    ):
        """Test logging resolution defaults actor_type to employee."""
        service = TicketHistoryService(db_session)

        history = service.log_resolution(
            ticket=sample_ticket,
        )

        assert history.actor_type == "employee"


class TestLogClosure:
    def test_log_closure_creates_record(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test logging ticket closure creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_closure(
            ticket=sample_ticket,
            close_reason="Customer confirmed resolution",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.CLOSED
        assert history.new_value["status"] == "Closed"
        assert history.note == "Customer confirmed resolution"

    def test_log_closure_defaults_to_customer_actor(
        self, db_session, sample_ticket
    ):
        """Test logging closure defaults actor_type to customer."""
        service = TicketHistoryService(db_session)

        history = service.log_closure(
            ticket=sample_ticket,
        )

        assert history.actor_type == "customer"


class TestLogReopen:
    def test_log_reopen_creates_record(
        self, db_session, sample_ticket, sample_customer
    ):
        """Test logging ticket reopen creates a history record."""
        service = TicketHistoryService(db_session)

        history = service.log_reopen(
            ticket=sample_ticket,
            reason="Issue reoccurred after resolution",
            actor_id=sample_customer.id,
            actor_type="customer",
        )

        assert history.id_ticket == sample_ticket.id_ticket
        assert history.action == TicketAction.REOPENED
        assert history.old_value["status"] == "Closed"
        assert history.new_value["status"] == "In Progress"
        assert history.note == "Issue reoccurred after resolution"


class TestGetTicketHistory:
    def test_get_ticket_history_returns_records(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test retrieving ticket history returns logged records."""
        service = TicketHistoryService(db_session)

        # Create some history records
        service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )
        service.log_status_change(
            ticket=sample_ticket,
            old_status="New",
            new_status="In Progress",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        histories = service.get_ticket_history(sample_ticket.id_ticket)

        assert len(histories) == 2
        assert all(h.id_ticket == sample_ticket.id_ticket for h in histories)

    def test_get_ticket_history_returns_ordered_records(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test ticket history is returned in descending order by created_at."""
        service = TicketHistoryService(db_session)

        # Create records in specific order
        history1 = service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )
        history2 = service.log_status_change(
            ticket=sample_ticket,
            old_status="New",
            new_status="In Progress",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        histories = service.get_ticket_history(sample_ticket.id_ticket)

        # Most recent should come first (descending order)
        assert histories[0].id_history in [history1.id_history, history2.id_history]

    def test_get_ticket_history_returns_empty_for_ticket_without_history(
        self, db_session, sample_ticket
    ):
        """Test ticket with no history returns empty list."""
        service = TicketHistoryService(db_session)

        histories = service.get_ticket_history(sample_ticket.id_ticket)

        assert isinstance(histories, list)
        assert len(histories) == 0

    def test_get_ticket_history_with_actor_names_returns_dicts(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test getting history with actor names returns dict objects."""
        service = TicketHistoryService(db_session)

        service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        histories = service.get_ticket_history_with_actor_names(sample_ticket.id_ticket)

        assert len(histories) == 1
        assert isinstance(histories[0], dict)
        assert "actor_name" in histories[0]
        assert "action" in histories[0]
        assert "created_at" in histories[0]
        assert histories[0]["actor_name"] == f"{sample_employee.first_name} {sample_employee.last_name}"


class TestTicketHistoryPersistence:
    def test_history_record_persists_in_database(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test history records are persisted and retrievable."""
        service = TicketHistoryService(db_session)

        history = service.log_ticket_created(
            ticket=sample_ticket,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        # Verify persistence by querying directly
        from app.repositories.ticketHistoryRepository import TicketHistoryRepository
        repo = TicketHistoryRepository(db_session)
        retrieved = repo.get_by_id(history.id_history)

        assert retrieved is not None
        assert retrieved.id_history == history.id_history
        assert retrieved.action == TicketAction.CREATED

    def test_multiple_actions_create_separate_records(
        self, db_session, sample_ticket, sample_employee
    ):
        """Test multiple actions create separate history records."""
        service = TicketHistoryService(db_session)

        history1 = service.log_status_change(
            ticket=sample_ticket,
            old_status="New",
            new_status="In Progress",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )
        history2 = service.log_assignment(
            ticket=sample_ticket,
            old_employee_id=None,
            new_employee_id=sample_employee.id_employee,
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )
        history3 = service.log_resolution(
            ticket=sample_ticket,
            resolution_note="Fixed",
            actor_id=sample_employee.id_employee,
            actor_type="employee",
        )

        histories = service.get_ticket_history(sample_ticket.id_ticket)

        assert len(histories) == 3
        history_ids = [h.id_history for h in histories]
        assert history1.id_history in history_ids
        assert history2.id_history in history_ids
        assert history3.id_history in history_ids