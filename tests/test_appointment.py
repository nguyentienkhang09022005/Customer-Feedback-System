"""
Unit tests for Appointment Scheduling Module.

Tests cover:
- Appointment creation by customer
- Appointment acceptance by employee
- Appointment rejection by employee (with reason)
- Appointment cancellation by customer
- Appointment listing (by ticket, by employee, pending)
- Validation rules (time in future, existing pending, etc.)
- Authorization checks (owner validation, employee validation)

Test flow:
1. Customer creates appointment request for a ticket with assigned employee
2. Employee receives notification and can accept/reject
3. Customer can cancel pending/accepted appointments
4. Only owner can perform actions on their appointments
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.appointmentService import AppointmentService
from app.schemas.appointmentSchema import AppointmentCreate, AppointmentAccept, AppointmentReject, AppointmentCancel
from app.models.appointment import Appointment
from app.models.human import Customer, Employee
from app.models.ticket import Ticket
from app.core.constants import AppointmentStatus, AppointmentConstants


# ============================================================================
# Appointment Creation Tests
# ============================================================================

class TestAppointmentCreation:
    """Tests for appointment creation functionality."""

    def test_create_appointment_success(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer,
        mock_notification_service
    ):
        """Test successful appointment creation."""
        service = AppointmentService(db_session)

        future_time = datetime.now(timezone.utc) + timedelta(days=1)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=future_time,
            reason="Need detailed consultation on my issue"
        )

        appointment = service.create_appointment(data, sample_customer.id_customer)

        assert appointment is not None
        assert appointment.id_ticket == sample_ticket_assigned.id_ticket
        assert appointment.id_customer == sample_customer.id_customer
        assert appointment.id_employee == sample_ticket_assigned.id_employee
        assert appointment.status == AppointmentStatus.PENDING
        assert appointment.reason == "Need detailed consultation on my issue"

    def test_create_appointment_ticket_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test appointment creation fails when ticket not found."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=uuid4(),
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "Không tìm thấy ticket" in str(exc_info.value)

    def test_create_appointment_deleted_ticket(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer
    ):
        """Test appointment creation fails for deleted ticket."""
        sample_ticket_assigned.is_deleted = True
        db_session.commit()

        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "đã bị xóa" in str(exc_info.value)

    def test_create_appointment_not_owner(
        self,
        db_session,
        sample_ticket_assigned
    ):
        """Test appointment creation fails when customer doesn't own ticket."""
        # Create another customer
        other_customer = Customer(
            id=uuid4(),
            username="othercust",
            email="other@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other",
            last_name="Customer",
            phone="2222222222",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH222222"
        )
        db_session.add(other_customer)
        db_session.commit()

        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, other_customer.id_customer)

        assert "không có quyền" in str(exc_info.value)

    def test_create_appointment_no_employee_assigned(
        self,
        db_session,
        sample_ticket,  # Unassigned ticket
        sample_customer
    ):
        """Test appointment creation fails when ticket has no employee."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "chưa có nhân viên đảm nhận" in str(exc_info.value)

    def test_create_appointment_resolved_ticket(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer
    ):
        """Test appointment creation fails for resolved ticket."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "đã được giải quyết hoặc đóng" in str(exc_info.value)

    def test_create_appointment_closed_ticket(
        self,
        db_session,
        sample_ticket_closed,
        sample_customer
    ):
        """Test appointment creation fails for closed ticket."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_closed.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "đã được giải quyết hoặc đóng" in str(exc_info.value)

    def test_create_appointment_past_time(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer
    ):
        """Test appointment creation fails for past time."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) - timedelta(days=1),  # Past
            reason="Test"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "lớn hơn thời gian hiện tại" in str(exc_info.value)

    def test_create_appointment_empty_reason(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer
    ):
        """Test appointment creation fails with empty reason."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason=""
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "Vui lòng cung cấp lý do" in str(exc_info.value)

    def test_create_appointment_whitespace_reason(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer
    ):
        """Test appointment creation fails with whitespace-only reason."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="   "  # Only whitespace
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "Vui lòng cung cấp lý do" in str(exc_info.value)

    def test_create_appointment_existing_pending(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer,
        sample_appointment
    ):
        """Test appointment creation fails when pending appointment exists."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Another appointment"
        )

        with pytest.raises(Exception) as exc_info:
            service.create_appointment(data, sample_customer.id_customer)

        assert "đã có lịch hẹn đang chờ xử lý" in str(exc_info.value)


# ============================================================================
# Appointment Acceptance Tests
# ============================================================================

class TestAppointmentAcceptance:
    """Tests for appointment acceptance by employee."""

    def test_accept_appointment_success(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test successful appointment acceptance."""
        service = AppointmentService(db_session)

        appointment = service.accept_appointment(
            sample_appointment.id_appointment,
            sample_employee.id_employee
        )

        assert appointment.status == AppointmentStatus.ACCEPTED

    def test_accept_appointment_not_found(
        self,
        db_session,
        sample_employee
    ):
        """Test acceptance fails for nonexistent appointment."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.accept_appointment(uuid4(), sample_employee.id_employee)

        assert "Không tìm thấy lịch hẹn" in str(exc_info.value)

    def test_accept_appointment_wrong_employee(
        self,
        db_session,
        sample_appointment
    ):
        """Test acceptance fails when employee is not the assignee."""
        # Create another employee
        other_employee = Employee(
            id=uuid4(),
            username="otheremp",
            email="otheremp@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other",
            last_name="Employee",
            phone="3333333333",
            type="employee",
            id_employee=uuid4(),
            employee_code="EMP999",
            role_name="Employee"
        )
        db_session.add(other_employee)
        db_session.commit()

        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.accept_appointment(
                sample_appointment.id_appointment,
                other_employee.id_employee
            )

        assert "không có quyền" in str(exc_info.value)

    def test_accept_already_accepted_appointment(
        self,
        db_session,
        sample_appointment_accepted,
        sample_employee
    ):
        """Test acceptance fails when appointment already accepted."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.accept_appointment(
                sample_appointment_accepted.id_appointment,
                sample_employee.id_employee
            )

        assert "không thể xác nhận" in str(exc_info.value)


# ============================================================================
# Appointment Rejection Tests
# ============================================================================

class TestAppointmentRejection:
    """Tests for appointment rejection by employee."""

    def test_reject_appointment_success(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test successful appointment rejection."""
        service = AppointmentService(db_session)

        appointment = service.reject_appointment(
            sample_appointment.id_appointment,
            sample_employee.id_employee,
            "Schedule conflict, please choose another time"
        )

        assert appointment.status == AppointmentStatus.REJECTED
        assert appointment.rejection_reason == "Schedule conflict, please choose another time"

    def test_reject_appointment_empty_reason(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test rejection fails with empty reason."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reject_appointment(
                sample_appointment.id_appointment,
                sample_employee.id_employee,
                ""
            )

        assert "Vui lòng cung cấp lý do" in str(exc_info.value)

    def test_reject_appointment_whitespace_reason(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test rejection fails with whitespace reason."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reject_appointment(
                sample_appointment.id_appointment,
                sample_employee.id_employee,
                "   "
            )

        assert "Vui lòng cung cấp lý do" in str(exc_info.value)

    def test_reject_appointment_not_found(
        self,
        db_session,
        sample_employee
    ):
        """Test rejection fails for nonexistent appointment."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reject_appointment(
                uuid4(),
                sample_employee.id_employee,
                "Some reason"
            )

        assert "Không tìm thấy lịch hẹn" in str(exc_info.value)

    def test_reject_already_rejected_appointment(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test rejection fails when already rejected."""
        # First reject the appointment
        sample_appointment.status = AppointmentStatus.REJECTED
        sample_appointment.rejection_reason = "First rejection"
        db_session.commit()

        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.reject_appointment(
                sample_appointment.id_appointment,
                sample_employee.id_employee,
                "Second rejection"
            )

        assert "không thể từ chối" in str(exc_info.value)


# ============================================================================
# Appointment Cancellation Tests
# ============================================================================

class TestAppointmentCancellation:
    """Tests for appointment cancellation by customer."""

    def test_cancel_appointment_pending_success(
        self,
        db_session,
        sample_appointment,
        sample_customer
    ):
        """Test successful cancellation of pending appointment."""
        service = AppointmentService(db_session)

        appointment = service.cancel_appointment(
            sample_appointment.id_appointment,
            sample_customer.id_customer
        )

        assert appointment.status == AppointmentStatus.CANCELLED

    def test_cancel_appointment_accepted_success(
        self,
        db_session,
        sample_appointment_accepted,
        sample_customer
    ):
        """Test successful cancellation of accepted appointment."""
        service = AppointmentService(db_session)

        appointment = service.cancel_appointment(
            sample_appointment_accepted.id_appointment,
            sample_customer.id_customer
        )

        assert appointment.status == AppointmentStatus.CANCELLED

    def test_cancel_appointment_not_owner(
        self,
        db_session,
        sample_appointment
    ):
        """Test cancellation fails when not the owner."""
        # Create another customer
        other_customer = Customer(
            id=uuid4(),
            username="othercust2",
            email="other2@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other2",
            last_name="Customer",
            phone="4444444444",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH444444"
        )
        db_session.add(other_customer)
        db_session.commit()

        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.cancel_appointment(
                sample_appointment.id_appointment,
                other_customer.id_customer
            )

        assert "không có quyền" in str(exc_info.value)

    def test_cancel_appointment_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test cancellation fails for nonexistent appointment."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.cancel_appointment(uuid4(), sample_customer.id_customer)

        assert "Không tìm thấy lịch hẹn" in str(exc_info.value)

    def test_cancel_rejected_appointment_fails(
        self,
        db_session,
        sample_appointment,
        sample_customer
    ):
        """Test cancellation fails for rejected appointment."""
        sample_appointment.status = AppointmentStatus.REJECTED
        sample_appointment.rejection_reason = "Cannot attend"
        db_session.commit()

        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.cancel_appointment(
                sample_appointment.id_appointment,
                sample_customer.id_customer
            )

        assert "không thể hủy" in str(exc_info.value)

    def test_cancel_completed_appointment_fails(
        self,
        db_session,
        sample_appointment,
        sample_customer
    ):
        """Test cancellation fails for completed appointment."""
        sample_appointment.status = AppointmentStatus.COMPLETED
        db_session.commit()

        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.cancel_appointment(
                sample_appointment.id_appointment,
                sample_customer.id_customer
            )

        assert "không thể hủy" in str(exc_info.value)


# ============================================================================
# Appointment Retrieval Tests
# ============================================================================

class TestAppointmentRetrieval:
    """Tests for retrieving appointments."""

    def test_get_appointment_by_id_success(
        self,
        db_session,
        sample_appointment
    ):
        """Test successful appointment retrieval by ID."""
        service = AppointmentService(db_session)

        appointment = service.get_appointment_by_id(sample_appointment.id_appointment)

        assert appointment is not None
        assert appointment.id_appointment == sample_appointment.id_appointment

    def test_get_appointment_by_id_not_found(
        self,
        db_session
    ):
        """Test retrieval fails for nonexistent appointment."""
        service = AppointmentService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.get_appointment_by_id(uuid4())

        assert "Không tìm thấy lịch hẹn" in str(exc_info.value)

    def test_get_appointments_by_ticket(
        self,
        db_session,
        sample_appointment
    ):
        """Test getting appointments for a ticket."""
        service = AppointmentService(db_session)

        appointments = service.get_appointments_by_ticket(sample_appointment.id_ticket)

        assert len(appointments) >= 1
        assert any(a.id_appointment == sample_appointment.id_appointment for a in appointments)

    def test_get_appointments_by_employee(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test getting appointments for an employee."""
        service = AppointmentService(db_session)

        appointments = service.get_appointments_by_employee(sample_employee.id_employee)

        assert len(appointments) >= 1

    def test_get_pending_appointments_by_employee(
        self,
        db_session,
        sample_appointment,
        sample_employee
    ):
        """Test getting pending appointments for an employee."""
        service = AppointmentService(db_session)

        appointments = service.get_pending_appointments_by_employee(sample_employee.id_employee)

        assert len(appointments) >= 1
        assert all(a.status == AppointmentStatus.PENDING for a in appointments)


# ============================================================================
# Appointment Constants Validation Tests
# ============================================================================

class TestAppointmentConstants:
    """Tests for appointment status constants."""

    def test_valid_statuses_list(
        self
    ):
        """Test all valid appointment statuses are defined."""
        expected_statuses = ["pending", "accepted", "rejected", "cancelled", "completed"]
        for status in expected_statuses:
            assert status in AppointmentConstants.VALID_STATUSES

    def test_cancelable_statuses(
        self
    ):
        """Test cancelable statuses only include pending and accepted."""
        assert "pending" in AppointmentConstants.CANCELABLE_STATUSES
        assert "accepted" in AppointmentConstants.CANCELABLE_STATUSES
        assert "rejected" not in AppointmentConstants.CANCELABLE_STATUSES
        assert "cancelled" not in AppointmentConstants.CANCELABLE_STATUSES
        assert "completed" not in AppointmentConstants.CANCELABLE_STATUSES


# ============================================================================
# Edge Cases
# ============================================================================

class TestAppointmentEdgeCases:
    """Edge case tests for appointment functionality."""

    def test_appointment_very_far_future(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer,
        mock_notification_service
    ):
        """Test appointment can be scheduled very far in the future."""
        service = AppointmentService(db_session)

        far_future = datetime.now(timezone.utc) + timedelta(days=365)  # 1 year

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=far_future,
            reason="Long-term planning meeting"
        )

        appointment = service.create_appointment(data, sample_customer.id_customer)

        assert appointment is not None
        assert appointment.status == AppointmentStatus.PENDING

    def test_appointment_very_long_reason(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer,
        mock_notification_service
    ):
        """Test appointment with very long reason."""
        service = AppointmentService(db_session)

        long_reason = "A" * 1000  # 1000 character reason

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason=long_reason
        )

        appointment = service.create_appointment(data, sample_customer.id_customer)

        assert appointment is not None
        assert len(appointment.reason) == 1000

    def test_multiple_appointments_same_customer_different_tickets(
        self,
        db_session,
        sample_customer,
        sample_employee,
        sample_ticket_assigned,
        mock_notification_service
    ):
        """Test customer can have multiple pending appointments for different tickets."""
        service = AppointmentService(db_session)

        # Create second ticket
        ticket2 = Ticket(
            id_ticket=uuid4(),
            title="Second issue",
            status="In Progress",
            id_customer=sample_customer.id_customer,
            id_employee=sample_employee.id_employee
        )
        db_session.add(ticket2)
        db_session.commit()

        # Create first appointment
        data1 = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="First appointment"
        )
        appt1 = service.create_appointment(data1, sample_customer.id_customer)

        # Create second appointment for different ticket
        data2 = AppointmentCreate(
            id_ticket=ticket2.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
            reason="Second appointment"
        )
        appt2 = service.create_appointment(data2, sample_customer.id_customer)

        assert appt1.status == AppointmentStatus.PENDING
        assert appt2.status == AppointmentStatus.PENDING

    def test_appointment_notification_sent_on_create(
        self,
        db_session,
        sample_ticket_assigned,
        sample_customer,
        mock_notification_service
    ):
        """Test notification is sent when appointment is created."""
        service = AppointmentService(db_session)

        data = AppointmentCreate(
            id_ticket=sample_ticket_assigned.id_ticket,
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=1),
            reason="Test notification"
        )

        service.create_appointment(data, sample_customer.id_customer)

        mock_notification_service.create_and_send.assert_called()
