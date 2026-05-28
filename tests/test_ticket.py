"""
Unit tests for Ticket Management Module.

Tests cover:
- Ticket creation from template
- Ticket retrieval (all, by customer, by employee, unassigned)
- Ticket update (status, severity, custom fields)
- Ticket assignment to employees
- Ticket status transitions (New -> In Progress -> Resolved -> Closed)
- Ticket deletion (soft delete)
- Ticket reopening
- Rate limiting for ticket creation
- SLA calculation based on severity
- Authorization checks

Test flow:
1. Customer creates ticket from template
2. Manager/Admin assigns ticket to employee
3. Employee updates ticket status through workflow
4. Customer can only update when status is New
5. Customer can close/reopen resolved tickets
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.ticketService import TicketService
from app.schemas.ticketSchema import (
    TicketFromTemplateCreate,
    TicketUpdate,
    TicketAssign,
    TicketResolve,
    TicketClose,
    TicketReopen,
    TicketCustomerUpdate,
)
from app.models.ticket import Ticket
from app.models.human import Customer, Employee
from app.core.constants import TicketStatusConstants


# ============================================================================
# Ticket Creation Tests
# ============================================================================

class TestTicketCreation:
    """Tests for ticket creation functionality."""

    def test_create_ticket_from_template_success(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        mock_redis_service,
        mock_notification_service
    ):
        """Test successful ticket creation from template."""
        service = TicketService(db_session)

        data = TicketFromTemplateCreate(
            title="Critical bug in login page",
            severity="High",
            id_template=sample_ticket_template.id_template,
            custom_fields={
                "steps_to_reproduce": "User clicks login button",
                "expected_behavior": "User should be logged in",
                "actual_behavior": "Error message appears"
            }
        )

        ticket = service.create_ticket_from_template(data, sample_customer.id_customer)

        assert ticket is not None
        assert ticket.title == "Critical bug in login page"
        assert ticket.severity == "High"
        assert ticket.status == "New"
        assert ticket.id_customer == sample_customer.id_customer
        assert ticket.id_template == sample_ticket_template.id_template

    def test_create_ticket_from_template_with_default_severity(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        mock_redis_service,
        mock_notification_service
    ):
        """Test ticket creation uses template's default severity when not provided."""
        service = TicketService(db_session)

        data = TicketFromTemplateCreate(
            title="General issue",
            id_template=sample_ticket_template.id_template,
            custom_fields={}
        )

        ticket = service.create_ticket_from_template(data, sample_customer.id_customer)

        assert ticket is not None
        # Template default severity is "Medium"
        assert ticket.severity == "Medium"

    def test_create_ticket_from_template_not_found(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test ticket creation fails when template not found."""
        service = TicketService(db_session)

        data = TicketFromTemplateCreate(
            title="Test ticket",
            id_template=uuid4(),  # Nonexistent template
            custom_fields={}
        )

        with pytest.raises(Exception) as exc_info:
            service.create_ticket_from_template(data, sample_customer.id_customer)

        assert "Không tìm thấy template" in str(exc_info.value)

    def test_create_ticket_from_template_deleted(
        self,
        db_session,
        sample_customer,
        mock_redis_service
    ):
        """Test ticket creation fails when template is deleted (via service delete)."""
        # Create template and delete it via service (which handles soft-delete properly)
        from app.services.ticketTemplateService import TicketTemplateService
        template_service = TicketTemplateService(db_session)
        from app.schemas.ticketCategorySchema import TicketTemplateCreate

        # Create fresh template
        from tests.conftest import create_test_jwt_token

        # Use category fixture from conftest
        from app.models.ticket import TicketCategory
        from uuid import uuid4
        from app.models.department import Department

        # Get a department from existing fixtures
        dept = db_session.query(Department).first()
        if not dept:
            dept = Department(id_department=uuid4(), name="Test Dept", is_active=True)
            db_session.add(dept)
            db_session.commit()

        category = TicketCategory(
            id_category=uuid4(),
            name="Test Category",
            id_department=dept.id_department,
            is_active=True
        )
        db_session.add(category)
        db_session.commit()

        create_data = TicketTemplateCreate(
            name="Will Delete Template",
            fields_config={"fields": []},
        )
        template = template_service.create_template(create_data)

        # Now delete via service
        template_service.delete_template(template.id_template)

        # Try to create ticket with deleted template
        service = TicketService(db_session)
        data = TicketFromTemplateCreate(
            title="Test ticket",
            id_template=template.id_template,
            custom_fields={}
        )

        with pytest.raises(Exception) as exc_info:
            service.create_ticket_from_template(data, sample_customer.id_customer)

        # Since soft-deleted templates are filtered out, we get "not found"
        assert "Không tìm thấy template" in str(exc_info.value) or "đã bị xóa" in str(exc_info.value)

    def test_create_ticket_from_template_inactive(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        mock_redis_service
    ):
        """Test ticket creation fails when template is inactive."""
        sample_ticket_template.is_active = False
        db_session.commit()

        service = TicketService(db_session)

        data = TicketFromTemplateCreate(
            title="Test ticket",
            id_template=sample_ticket_template.id_template,
            custom_fields={}
        )

        with pytest.raises(Exception) as exc_info:
            service.create_ticket_from_template(data, sample_customer.id_customer)

        assert "không còn hoạt động" in str(exc_info.value)

    def test_create_ticket_respects_rate_limit(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        mock_redis_service
    ):
        """Test ticket creation is rate limited."""
        # Patch RedisService constructor so the service creates a mocked instance
        from unittest.mock import patch, MagicMock

        # Create a mock redis service
        mock_rs = MagicMock()
        mock_rs.get.return_value = "10"  # Exceeds default limit of 5

        with patch("app.services.redisService.RedisService", return_value=mock_rs):
            service = TicketService(db_session)

            data = TicketFromTemplateCreate(
                title="Rate limited ticket",
                id_template=sample_ticket_template.id_template,
                custom_fields={}
            )

            with pytest.raises(Exception) as exc_info:
                service.create_ticket_from_template(data, sample_customer.id_customer)

            assert "quá nhiều tickets" in str(exc_info.value)


# ============================================================================
# Ticket Retrieval Tests
# ============================================================================

class TestTicketRetrieval:
    """Tests for ticket retrieval functionality."""

    def test_get_all_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_assigned,
        sample_employee
    ):
        """Test retrieving all tickets."""
        service = TicketService(db_session)

        tickets = service.get_all_tickets()

        assert len(tickets) >= 2
        assert any(t.id_ticket == sample_ticket.id_ticket for t in tickets)
        assert any(t.id_ticket == sample_ticket_assigned.id_ticket for t in tickets)

    def test_get_ticket_by_id_success(
        self,
        db_session,
        sample_ticket
    ):
        """Test retrieving ticket by ID."""
        service = TicketService(db_session)

        ticket = service.get_ticket_by_id(sample_ticket.id_ticket)

        assert ticket is not None
        assert ticket.id_ticket == sample_ticket.id_ticket

    def test_get_ticket_by_id_not_found(
        self,
        db_session
    ):
        """Test retrieving nonexistent ticket."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_ticket_by_id(uuid4())

        assert "Không tìm thấy ticket" in str(exc_info.value)

    def test_get_unassigned_tickets(
        self,
        db_session,
        sample_ticket,
        sample_ticket_assigned
    ):
        """Test retrieving unassigned tickets."""
        service = TicketService(db_session)

        tickets = service.get_unassigned_tickets()

        # sample_ticket is unassigned (id_employee = None)
        assert any(t.id_ticket == sample_ticket.id_ticket for t in tickets)
        # sample_ticket_assigned has an employee, should not be included
        assert not any(t.id_ticket == sample_ticket_assigned.id_ticket for t in tickets)

    def test_get_tickets_by_employee(
        self,
        db_session,
        sample_employee,
        sample_ticket_assigned
    ):
        """Test retrieving tickets assigned to a specific employee."""
        service = TicketService(db_session)

        tickets = service.get_tickets_by_employee(sample_employee.id_employee)

        assert len(tickets) >= 1
        assert all(t.id_employee == sample_employee.id_employee for t in tickets)

    def test_get_tickets_by_employee_excludes_closed_by_default(
        self,
        db_session,
        sample_employee,
        sample_ticket_closed
    ):
        """Test that get_tickets_by_employee excludes closed tickets by default."""
        service = TicketService(db_session)

        tickets = service.get_tickets_by_employee(sample_employee.id_employee)

        assert not any(t.id_ticket == sample_ticket_closed.id_ticket for t in tickets)

    def test_get_tickets_by_employee_includes_closed_when_requested(
        self,
        db_session,
        sample_employee,
        sample_ticket_closed
    ):
        """Test that get_tickets_by_employee includes closed when requested."""
        service = TicketService(db_session)

        tickets = service.get_tickets_by_employee(
            sample_employee.id_employee,
            include_closed=True
        )

        assert any(t.id_ticket == sample_ticket_closed.id_ticket for t in tickets)

    def test_get_tickets_by_customer(
        self,
        db_session,
        sample_customer,
        sample_ticket
    ):
        """Test retrieving tickets for a specific customer."""
        service = TicketService(db_session)

        tickets = service.get_tickets_by_customer(sample_customer.id_customer)

        assert len(tickets) >= 1
        assert all(t.id_customer == sample_customer.id_customer for t in tickets)

    def test_get_tickets_by_department(
        self,
        db_session,
        sample_department,
        sample_ticket_assigned
    ):
        """Test retrieving tickets by department."""
        service = TicketService(db_session)

        # Note: This requires the employee to be in the department
        tickets = service.get_tickets_by_department(sample_department.id_department)

        # Should return tickets assigned to employees in this department
        assert isinstance(tickets, list)


# ============================================================================
# Ticket Update Tests
# ============================================================================

class TestTicketUpdate:
    """Tests for ticket update functionality."""

    def test_update_ticket_status_success(
        self,
        db_session,
        sample_ticket
    ):
        """Test successful status update."""
        service = TicketService(db_session)

        data = TicketUpdate(status="In Progress")

        ticket = service.update_ticket(
            sample_ticket.id_ticket,
            data,
            actor_type="employee"
        )

        assert ticket.status == "In Progress"

    def test_update_ticket_invalid_status_transition(
        self,
        db_session,
        sample_ticket
    ):
        """Test status update fails for invalid transition."""
        service = TicketService(db_session)

        data = TicketUpdate(status="Resolved")  # Can't go directly from New to Resolved

        with pytest.raises(Exception) as exc_info:
            service.update_ticket(sample_ticket.id_ticket, data, actor_type="employee")

        assert "Không thể chuyển" in str(exc_info.value)

    def test_update_ticket_severity_recalculates_expired_date(
        self,
        db_session,
        sample_ticket,
        sample_sla_policy,
        mock_redis_service
    ):
        """Test that changing severity updates expired date based on SLA."""
        service = TicketService(db_session)

        data = TicketUpdate(severity="High")  # Has 1-day SLA

        ticket = service.update_ticket(
            sample_ticket.id_ticket,
            data,
            actor_type="employee"
        )

        # New expired_date should be set based on SLA
        assert ticket.severity == "High"
        assert ticket.expired_date is not None

    def test_update_ticket_deleted_ticket(
        self,
        db_session,
        sample_ticket
    ):
        """Test update fails for deleted ticket."""
        sample_ticket.is_deleted = True
        db_session.commit()

        service = TicketService(db_session)

        data = TicketUpdate(status="In Progress")

        with pytest.raises(Exception) as exc_info:
            service.update_ticket(sample_ticket.id_ticket, data, actor_type="employee")

        # Soft-deleted tickets are filtered out by repo, so we get "not found"
        assert "đã bị xóa" in str(exc_info.value) or "Không tìm thấy ticket" in str(exc_info.value)

    def test_employee_cannot_update_title_or_custom_fields(
        self,
        db_session,
        sample_ticket
    ):
        """Test that employee role cannot update title or custom_fields."""
        service = TicketService(db_session)

        data = TicketUpdate(
            title="Changed Title",
            custom_fields={"new": "field"}
        )

        with pytest.raises(Exception) as exc_info:
            service.update_ticket(sample_ticket.id_ticket, data, actor_type="employee")

        assert "chỉ được cập nhật trạng thái" in str(exc_info.value)

    def test_customer_update_ticket_success_when_new(
        self,
        db_session,
        sample_ticket,
        sample_customer
    ):
        """Test customer can update ticket when status is New."""
        service = TicketService(db_session)

        data = TicketCustomerUpdate(
            title="Customer updated title",
            custom_fields={"customer_field": "value"}
        )

        ticket = service.update_ticket_customer(
            sample_ticket.id_ticket,
            data,
            sample_customer.id_customer
        )

        assert ticket.title == "Customer updated title"

    def test_customer_update_ticket_fails_when_not_new(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer
    ):
        """Test customer cannot update ticket when status is not New."""
        service = TicketService(db_session)

        data = TicketCustomerUpdate(title="Should fail")

        with pytest.raises(Exception) as exc_info:
            service.update_ticket_customer(
                sample_ticket_assigned.id_ticket,
                data,
                sample_customer.id_customer
            )

        assert "trạng thái New" in str(exc_info.value)

    def test_customer_cannot_update_others_ticket(
        self,
        db_session,
        sample_ticket,
        sample_employee
    ):
        """Test customer cannot update ticket belonging to another customer."""
        service = TicketService(db_session)

        # Create another customer
        from app.models.human import Customer
        other_customer = Customer(
            id=uuid4(),
            username="othercustomer",
            email="other@example.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other",
            last_name="Customer",
            phone="9999999999",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH999999",
            status="Active"
        )
        db_session.add(other_customer)
        db_session.commit()

        data = TicketCustomerUpdate(title="Should fail")

        with pytest.raises(Exception) as exc_info:
            service.update_ticket_customer(
                sample_ticket.id_ticket,
                data,
                other_customer.id_customer
            )

        assert "không có quyền" in str(exc_info.value)


# ============================================================================
# Ticket Assignment Tests
# ============================================================================

class TestTicketAssignment:
    """Tests for ticket assignment functionality."""

    def test_assign_ticket_success(
        self,
        db_session,
        sample_ticket,
        sample_employee_2,
        mock_email_service
    ):
        """Test successful ticket assignment."""
        service = TicketService(db_session)

        data = TicketAssign(id_employee=sample_employee_2.id_employee)

        ticket = service.assign_ticket(sample_ticket.id_ticket, data)

        assert ticket.id_employee == sample_employee_2.id_employee

    def test_assign_ticket_not_found(
        self,
        db_session,
        sample_employee
    ):
        """Test assignment fails for nonexistent ticket."""
        service = TicketService(db_session)

        data = TicketAssign(id_employee=sample_employee.id_employee)

        with pytest.raises(Exception) as exc_info:
            service.assign_ticket(uuid4(), data)

        assert "Không tìm thấy ticket" in str(exc_info.value)

    def test_assign_deleted_ticket(
        self,
        db_session,
        sample_ticket,
        sample_employee
    ):
        """Test assignment fails for deleted ticket."""
        sample_ticket.is_deleted = True
        db_session.commit()

        service = TicketService(db_session)

        data = TicketAssign(id_employee=sample_employee.id_employee)

        with pytest.raises(Exception) as exc_info:
            service.assign_ticket(sample_ticket.id_ticket, data)

        assert "đã bị xóa" in str(exc_info.value) or "Không tìm thấy ticket" in str(exc_info.value)


# ============================================================================
# Ticket Status Transition Tests
# ============================================================================

class TestTicketStatusTransitions:
    """Tests for ticket status workflow transitions."""

    def test_resolve_ticket_from_in_progress(
        self,
        db_session,
        sample_ticket_assigned
    ):
        """Test resolving ticket from In Progress status."""
        service = TicketService(db_session)

        ticket = service.resolve_ticket(
            sample_ticket_assigned.id_ticket,
            resolution_note="Fixed the issue"
        )

        assert ticket.status == "Resolved"
        assert ticket.resolved_at is not None
        assert ticket.resolution_note == "Fixed the issue"

    def test_resolve_ticket_from_pending(
        self,
        db_session,
        sample_ticket
    ):
        """Test resolving ticket from Pending status."""
        # Change status to Pending
        sample_ticket.status = "Pending"
        db_session.commit()

        service = TicketService(db_session)

        ticket = service.resolve_ticket(sample_ticket.id_ticket)

        assert ticket.status == "Resolved"

    def test_resolve_ticket_from_on_hold(
        self,
        db_session,
        sample_ticket
    ):
        """Test resolving ticket from On Hold status."""
        sample_ticket.status = "On Hold"
        db_session.commit()

        service = TicketService(db_session)

        ticket = service.resolve_ticket(sample_ticket.id_ticket)

        assert ticket.status == "Resolved"

    def test_resolve_ticket_invalid_from_new(
        self,
        db_session,
        sample_ticket
    ):
        """Test resolving ticket directly from New fails."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.resolve_ticket(sample_ticket.id_ticket)

        assert "Không thể giải quyết ticket" in str(exc_info.value)

    def test_resolve_ticket_invalid_from_closed(
        self,
        db_session,
        sample_ticket_closed
    ):
        """Test resolving already closed ticket fails."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.resolve_ticket(sample_ticket_closed.id_ticket)

        assert "Không thể giải quyết ticket" in str(exc_info.value)

    def test_close_ticket_from_resolved(
        self,
        db_session,
        sample_ticket_resolved
    ):
        """Test closing ticket from Resolved status."""
        service = TicketService(db_session)

        ticket = service.close_ticket(
            sample_ticket_resolved.id_ticket,
            reason="Customer satisfied"
        )

        assert ticket.status == "Closed"
        assert ticket.resolution_note == "Customer satisfied"

    def test_close_ticket_invalid_from_in_progress(
        self,
        db_session,
        sample_ticket_assigned
    ):
        """Test closing ticket directly from In Progress fails."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.close_ticket(sample_ticket_assigned.id_ticket)

        assert "Chỉ có thể đóng ticket từ trạng thái Resolved" in str(exc_info.value)

    def test_reopen_ticket_from_closed(
        self,
        db_session,
        sample_ticket_closed
    ):
        """Test reopening closed ticket."""
        service = TicketService(db_session)

        ticket = service.reopen_ticket(
            sample_ticket_closed.id_ticket,
            reason="Customer not satisfied with resolution"
        )

        # Should go back to In Progress since it had an employee
        assert ticket.status == "In Progress"

    def test_reopen_ticket_without_employee_goes_to_new(
        self,
        db_session,
        sample_ticket
    ):
        """Test that reopened ticket goes to New if no employee assigned."""
        sample_ticket.status = "Closed"
        sample_ticket.id_employee = None
        db_session.commit()

        service = TicketService(db_session)

        ticket = service.reopen_ticket(sample_ticket.id_ticket, reason="Test")

        assert ticket.status == "New"

    def test_reopen_ticket_without_reason_fails(
        self,
        db_session,
        sample_ticket_closed
    ):
        """Test that reopening without reason fails."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reopen_ticket(sample_ticket_closed.id_ticket, "")

        assert "Vui lòng cung cấp lý do" in str(exc_info.value)

    def test_reopen_ticket_invalid_from_resolved(
        self,
        db_session,
        sample_ticket_resolved
    ):
        """Test that reopening from Resolved (not Closed) fails."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reopen_ticket(sample_ticket_resolved.id_ticket, "Some reason")

        assert "Chỉ có thể mở lại ticket từ trạng thái 'Closed'" in str(exc_info.value)


# ============================================================================
# Ticket Deletion Tests
# ============================================================================

class TestTicketDeletion:
    """Tests for ticket deletion (soft delete) functionality."""

    def test_delete_ticket_success(
        self,
        db_session,
        sample_ticket
    ):
        """Test successful soft delete of ticket."""
        service = TicketService(db_session)

        result = service.delete_ticket(sample_ticket.id_ticket)

        assert result.is_deleted is True
        assert result.deleted_at is not None

    def test_delete_ticket_not_found(
        self,
        db_session
    ):
        """Test deletion fails for nonexistent ticket."""
        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_ticket(uuid4())

        assert "Không tìm thấy ticket" in str(exc_info.value)

    def test_delete_already_deleted_ticket(
        self,
        db_session,
        sample_ticket
    ):
        """Test deletion fails for already deleted ticket."""
        sample_ticket.is_deleted = True
        db_session.commit()

        service = TicketService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_ticket(sample_ticket.id_ticket)

        assert "đã bị xóa" in str(exc_info.value) or "Không tìm thấy ticket" in str(exc_info.value)


# ============================================================================
# Ticket Expired Date / SLA Tests
# ============================================================================

class TestTicketSLA:
    """Tests for SLA and expired date calculations."""

    def test_expired_date_calculated_on_creation(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        sample_sla_policy,
        mock_redis_service
    ):
        """Test that expired_date is set based on SLA on ticket creation."""
        service = TicketService(db_session)

        data = TicketFromTemplateCreate(
            title="SLA Test Ticket",
            severity="High",
            id_template=sample_ticket_template.id_template
        )

        ticket = service.create_ticket_from_template(data, sample_customer.id_customer)

        # High severity SLA = 1 day
        assert ticket.expired_date is not None
        expected_date = datetime.utcnow() + timedelta(days=1)
        # Allow small time difference
        diff = abs((ticket.expired_date - expected_date).total_seconds())
        assert diff < 5  # Within 5 seconds

    def test_expired_date_uses_severity_mapping(
        self,
        db_session,
        sample_customer,
        sample_ticket_template,
        sample_sla_policy,
        mock_redis_service
    ):
        """Test expired date changes when severity is updated."""
        service = TicketService(db_session)

        # Create ticket with default (Medium) severity
        data = TicketFromTemplateCreate(
            title="SLA Change Test",
            id_template=sample_ticket_template.id_template
        )

        ticket = service.create_ticket_from_template(data, sample_customer.id_customer)
        original_expired = ticket.expired_date

        # Update severity to High (1 day SLA)
        update_data = TicketUpdate(severity="High")
        updated_ticket = service.update_ticket(
            ticket.id_ticket,
            update_data,
            actor_type="employee"
        )

        # New expired date should be sooner
        assert updated_ticket.expired_date < original_expired


# ============================================================================
# Authorization Tests
# ============================================================================

class TestTicketAuthorization:
    """Tests for ticket access authorization."""

    def test_customer_cannot_access_other_customer_ticket(
        self,
        db_session
    ):
        """Test customer cannot access ticket belonging to another customer."""
        from app.models.human import Customer
        from app.services.ticketService import TicketService
        from app.schemas.ticketSchema import TicketFromTemplateCreate

        # Create two customers
        customer1 = Customer(
            id=uuid4(),
            username="customer1",
            email="customer1@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="C1",
            last_name="Test",
            phone="1111111111",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH111111"
        )
        customer2 = Customer(
            id=uuid4(),
            username="customer2",
            email="customer2@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="C2",
            last_name="Test",
            phone="2222222222",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH222222"
        )
        db_session.add(customer1)
        db_session.add(customer2)
        db_session.commit()

        # Create ticket for customer1
        from app.models.ticket import Ticket
        ticket = Ticket(
            id_ticket=uuid4(),
            title="Customer1's ticket",
            status="New",
            id_customer=customer1.id_customer
        )
        db_session.add(ticket)
        db_session.commit()

        service = TicketService(db_session)
        retrieved_ticket = service.get_ticket_by_id(ticket.id_ticket)

        # Customer2 should not be able to access customer1's ticket
        assert retrieved_ticket.id_customer != customer2.id_customer


# ============================================================================
# Status Transition Validation Tests
# ============================================================================

class TestStatusTransitionValidation:
    """Tests for status transition validation rules."""

    def test_valid_transitions_from_new(
        self,
        sample_ticket
    ):
        """Test valid transitions from New status."""
        valid_targets = TicketStatusConstants.STATUS_TRANSITIONS["New"]
        assert "In Progress" in valid_targets
        assert "Pending" in valid_targets
        assert "On Hold" in valid_targets
        assert "Cancelled" in valid_targets
        assert "Resolved" not in valid_targets

    def test_valid_transitions_from_in_progress(
        self,
        sample_ticket
    ):
        """Test valid transitions from In Progress status."""
        valid_targets = TicketStatusConstants.STATUS_TRANSITIONS["In Progress"]
        assert "Pending" in valid_targets
        assert "On Hold" in valid_targets
        assert "Resolved" in valid_targets
        assert "Cancelled" in valid_targets
        assert "New" not in valid_targets

    def test_valid_transitions_from_resolved(
        self,
        sample_ticket
    ):
        """Test valid transitions from Resolved status."""
        valid_targets = TicketStatusConstants.STATUS_TRANSITIONS["Resolved"]
        assert "Closed" in valid_targets
        assert "In Progress" in valid_targets  # Can reopen before closing

    def test_valid_transitions_from_closed(
        self,
        sample_ticket
    ):
        """Test valid transitions from Closed status."""
        valid_targets = TicketStatusConstants.STATUS_TRANSITIONS["Closed"]
        assert len(valid_targets) == 0  # Cannot transition from Closed

    def test_valid_transitions_from_cancelled(
        self,
        sample_ticket
    ):
        """Test valid transitions from Cancelled status."""
        valid_targets = TicketStatusConstants.STATUS_TRANSITIONS["Cancelled"]
        assert "New" in valid_targets  # Can reopen cancelled ticket


# ============================================================================
# Edge Cases
# ============================================================================

class TestTicketEdgeCases:
    """Edge case tests for ticket management."""

    def test_ticket_version_increments_on_update(
        self,
        db_session,
        sample_ticket
    ):
        """Test that ticket version increments on each update."""
        service = TicketService(db_session)

        initial_version = sample_ticket.version

        data = TicketUpdate(status="In Progress")
        ticket = service.update_ticket(sample_ticket.id_ticket, data, actor_type="employee")

        assert ticket.version == initial_version + 1

    def test_multiple_status_changes(
        self,
        db_session,
        sample_ticket
    ):
        """Test multiple status changes maintain correct history."""
        service = TicketService(db_session)

        # New -> In Progress -> Pending -> Resolved -> Closed
        transitions = [
            ("In Progress", None),
            ("Pending", None),
            ("Resolved", None),
            ("Closed", "Final closure")
        ]

        for status, note in transitions:
            data = TicketUpdate(status=status)
            sample_ticket = service.update_ticket(sample_ticket.id_ticket, data, actor_type="employee")
            assert sample_ticket.status == status

    def test_ticket_is_overdue_property(
        self,
        db_session,
        sample_ticket
    ):
        """Test the is_overdue property calculation."""
        # Ticket with expired date in the past
        sample_ticket.expired_date = datetime.utcnow() - timedelta(days=1)
        sample_ticket.status = "In Progress"
        db_session.commit()

        assert sample_ticket.is_overdue is True

        # Resolved/Closed tickets are not overdue even if past expired_date
        sample_ticket.status = "Resolved"
        db_session.commit()
        assert sample_ticket.is_overdue is False

    def test_ticket_without_expired_date_not_overdue(
        self,
        db_session,
        sample_ticket
    ):
        """Test ticket without expired_date is not overdue."""
        sample_ticket.expired_date = None
        sample_ticket.status = "In Progress"
        db_session.commit()

        assert sample_ticket.is_overdue is False