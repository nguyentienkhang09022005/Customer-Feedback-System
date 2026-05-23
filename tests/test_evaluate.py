"""
Unit tests for Evaluation/CSAT (Customer Satisfaction) Module.

Tests cover:
- Creating evaluations for tickets
- Retrieving evaluations by ticket
- Updating evaluations by customer
- Deleting evaluations by customer
- Employee CSAT score calculation
- Star rating validation (1-5)
- Authorization checks

Test flow:
1. Customer creates evaluation after ticket is resolved
2. Evaluation includes star rating (1-5) and optional comment
3. Employee's CSAT score is recalculated based on all evaluations
4. Customer can update/delete their own evaluations
5. Only ticket owner can evaluate
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import uuid4

from app.services.evaluateService import EvaluateService
from app.schemas.evaluateSchema import EvaluateCreate, EvaluateUpdate
from app.models.interaction import Evaluate
from app.models.human import Customer, Employee
from app.models.ticket import Ticket


# ============================================================================
# Evaluation Creation Tests
# ============================================================================

class TestEvaluationCreation:
    """Tests for creating evaluations."""

    def test_create_evaluation_success(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test successful evaluation creation."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5,
            comment="Excellent service, very helpful support team!"
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate is not None
        assert evaluate.star == 5
        assert evaluate.comment == "Excellent service, very helpful support team!"
        assert evaluate.id_ticket == sample_ticket_resolved.id_ticket
        assert evaluate.id_customer == sample_customer.id_customer

    def test_create_evaluation_1_star(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation with 1 star (lowest rating)."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=1,
            comment="Very poor service"
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.star == 1

    def test_create_evaluation_5_stars(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation with 5 stars (highest rating)."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5,
            comment="Outstanding support!"
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.star == 5

    def test_create_evaluation_no_comment(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation creation without comment."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=4
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate is not None
        assert evaluate.star == 4
        assert evaluate.comment is None

    def test_create_evaluation_ticket_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test evaluation creation fails for nonexistent ticket."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=uuid4(),
            star=5
        )

        with pytest.raises(Exception) as exc_info:
            service.create_evaluate(data, sample_customer.id_customer)

        assert "Không tìm thấy Ticket" in str(exc_info.value)

    def test_create_evaluation_updates_employee_csat(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test that creating evaluation updates employee's CSAT score."""
        service = EvaluateService(db_session)

        # Create first evaluation
        data1 = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5,
            comment="Great!"
        )
        service.create_evaluate(data1, sample_customer.id_customer)

        # Check employee's CSAT score was updated
        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 5.0


# ============================================================================
# Evaluation Retrieval Tests
# ============================================================================

class TestEvaluationRetrieval:
    """Tests for retrieving evaluations."""

    def test_get_evaluates_by_ticket(
        self,
        db_session,
        sample_ticket_resolved,
        sample_evaluate
    ):
        """Test getting evaluations for a ticket."""
        service = EvaluateService(db_session)

        evaluates = service.get_evaluates_by_ticket(sample_ticket_resolved.id_ticket)

        assert len(evaluates) >= 1
        assert any(e.id_evaluate == sample_evaluate.id_evaluate for e in evaluates)

    def test_get_evaluates_by_ticket_none_exist(
        self,
        db_session,
        sample_ticket_assigned
    ):
        """Test getting evaluations when none exist for ticket."""
        service = EvaluateService(db_session)

        evaluates = service.get_evaluates_by_ticket(sample_ticket_assigned.id_ticket)

        assert len(evaluates) == 0


# ============================================================================
# Evaluation Update Tests
# ============================================================================

class TestEvaluationUpdate:
    """Tests for updating evaluations."""

    def test_update_evaluation_success(
        self,
        db_session,
        sample_evaluate,
        sample_customer
    ):
        """Test successful evaluation update."""
        service = EvaluateService(db_session)

        data = EvaluateUpdate(
            star=4,
            comment="Updated: Good service but could be faster"
        )

        evaluate = service.update_evaluate(
            sample_evaluate.id_evaluate,
            data,
            sample_customer.id_customer
        )

        assert evaluate.star == 4
        assert evaluate.comment == "Updated: Good service but could be faster"

    def test_update_evaluation_star_only(
        self,
        db_session,
        sample_evaluate,
        sample_customer
    ):
        """Test updating only the star rating."""
        service = EvaluateService(db_session)

        data = EvaluateUpdate(star=3)

        evaluate = service.update_evaluate(
            sample_evaluate.id_evaluate,
            data,
            sample_customer.id_customer
        )

        assert evaluate.star == 3
        # Comment should remain unchanged
        assert evaluate.comment == sample_evaluate.comment

    def test_update_evaluation_comment_only(
        self,
        db_session,
        sample_evaluate,
        sample_customer
    ):
        """Test updating only the comment."""
        service = EvaluateService(db_session)

        original_star = sample_evaluate.star
        data = EvaluateUpdate(comment="Only the comment changed")

        evaluate = service.update_evaluate(
            sample_evaluate.id_evaluate,
            data,
            sample_customer.id_customer
        )

        assert evaluate.star == original_star
        assert evaluate.comment == "Only the comment changed"

    def test_update_evaluation_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test update fails for nonexistent evaluation."""
        service = EvaluateService(db_session)

        data = EvaluateUpdate(star=5)

        with pytest.raises(Exception) as exc_info:
            service.update_evaluate(uuid4(), data, sample_customer.id_customer)

        assert "Không tìm thấy đánh giá" in str(exc_info.value)

    def test_update_evaluation_not_owner(
        self,
        db_session,
        sample_evaluate
    ):
        """Test update fails when customer is not the evaluation owner."""
        # Create another customer
        other_customer = Customer(
            id=uuid4(),
            username="othercust3",
            email="other3@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other3",
            last_name="Customer",
            phone="5555555555",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH555555"
        )
        db_session.add(other_customer)
        db_session.commit()

        service = EvaluateService(db_session)

        data = EvaluateUpdate(star=1)

        with pytest.raises(Exception) as exc_info:
            service.update_evaluate(
                sample_evaluate.id_evaluate,
                data,
                other_customer.id_customer
            )

        assert "không có quyền chỉnh sửa" in str(exc_info.value)


# ============================================================================
# Evaluation Deletion Tests
# ============================================================================

class TestEvaluationDeletion:
    """Tests for deleting evaluations."""

    def test_delete_evaluation_success(
        self,
        db_session,
        sample_evaluate,
        sample_customer
    ):
        """Test successful evaluation deletion."""
        service = EvaluateService(db_session)

        service.delete_evaluate(sample_evaluate.id_evaluate, sample_customer.id_customer)

        # Verify evaluation is deleted
        evaluate = db_session.query(Evaluate).filter(
            Evaluate.id_evaluate == sample_evaluate.id_evaluate
        ).first()
        assert evaluate is None

    def test_delete_evaluation_not_found(
        self,
        db_session,
        sample_customer
    ):
        """Test deletion fails for nonexistent evaluation."""
        service = EvaluateService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_evaluate(uuid4(), sample_customer.id_customer)

        assert "Không tìm thấy đánh giá" in str(exc_info.value)

    def test_delete_evaluation_not_owner(
        self,
        db_session,
        sample_evaluate
    ):
        """Test deletion fails when customer is not the evaluation owner."""
        # Create another customer
        other_customer = Customer(
            id=uuid4(),
            username="othercust4",
            email="other4@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Other4",
            last_name="Customer",
            phone="6666666666",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH666666"
        )
        db_session.add(other_customer)
        db_session.commit()

        service = EvaluateService(db_session)

        with pytest.raises(Exception) as exc_info:
            service.delete_evaluate(
                sample_evaluate.id_evaluate,
                other_customer.id_customer
            )

        assert "không có quyền xóa" in str(exc_info.value)


# ============================================================================
# Employee CSAT Score Calculation Tests
# ============================================================================

class TestEmployeeCSATScore:
    """Tests for employee CSAT score calculation."""

    def test_csat_score_single_evaluation(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test CSAT score with single evaluation."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5
        )
        service.create_evaluate(data, sample_customer.id_customer)

        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 5.0

    def test_csat_score_multiple_evaluations(
        self,
        db_session,
        sample_employee,
        mock_notification_service
    ):
        """Test CSAT score calculation with multiple evaluations."""
        # Create multiple tickets with same employee
        tickets = []
        for i in range(3):
            ticket = Ticket(
                id_ticket=uuid4(),
                title=f"Issue {i}",
                status="Resolved",
                resolved_at=datetime.utcnow(),
                id_employee=sample_employee.id_employee,
                id_customer=uuid4()
            )
            db_session.add(ticket)
            tickets.append(ticket)
        db_session.commit()

        # Create evaluations: 5, 4, 3 stars = average 4.0
        customer_ids = []
        for i, ticket in enumerate(tickets):
            customer = Customer(
                id=uuid4(),
                username=f"cust{i}",
                email=f"cust{i}@test.com",
                password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
                first_name=f"C{i}",
                last_name="Test",
                phone=f"77777777{i}",
                type="customer",
                id_customer=uuid4(),
                customer_code=f"KH7777{i}"
            )
            db_session.add(customer)
            customer_ids.append(customer)
        db_session.commit()

        service = EvaluateService(db_session)

        # Create evaluations: 5, 4, 3
        service.create_evaluate(EvaluateCreate(id_ticket=tickets[0].id_ticket, star=5), customer_ids[0].id_customer)
        service.create_evaluate(EvaluateCreate(id_ticket=tickets[1].id_ticket, star=4), customer_ids[1].id_customer)
        service.create_evaluate(EvaluateCreate(id_ticket=tickets[2].id_ticket, star=3), customer_ids[2].id_customer)

        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 4.0  # (5+4+3)/3 = 4.0

    def test_csat_score_no_evaluations(
        self,
        db_session,
        sample_employee
    ):
        """Test CSAT score is 0 when no evaluations exist."""
        service = EvaluateService(db_session)

        # Create a ticket without evaluation
        ticket = Ticket(
            id_ticket=uuid4(),
            title="No evaluation ticket",
            status="Resolved",
            id_employee=sample_employee.id_employee,
            id_customer=uuid4()
        )
        db_session.add(ticket)
        db_session.commit()

        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 0.0

    def test_csat_score_updates_on_new_evaluation(
        self,
        db_session,
        sample_employee,
        mock_notification_service
    ):
        """Test CSAT score updates when new evaluation is added."""
        # Setup: Create ticket and customer
        ticket = Ticket(
            id_ticket=uuid4(),
            title="First ticket",
            status="Resolved",
            resolved_at=datetime.utcnow(),
            id_employee=sample_employee.id_employee,
            id_customer=uuid4()
        )
        db_session.add(ticket)
        db_session.commit()

        customer = Customer(
            id=uuid4(),
            username="csatcust1",
            email="csat1@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Csat1",
            last_name="Test",
            phone="8888888881",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH888881"
        )
        db_session.add(customer)
        db_session.commit()

        service = EvaluateService(db_session)

        # First evaluation: 5 stars
        service.create_evaluate(EvaluateCreate(id_ticket=ticket.id_ticket, star=5), customer.id_customer)
        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 5.0

        # Create another ticket and evaluation
        ticket2 = Ticket(
            id_ticket=uuid4(),
            title="Second ticket",
            status="Resolved",
            resolved_at=datetime.utcnow(),
            id_employee=sample_employee.id_employee,
            id_customer=uuid4()
        )
        db_session.add(ticket2)
        db_session.commit()

        customer2 = Customer(
            id=uuid4(),
            username="csatcust2",
            email="csat2@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Csat2",
            last_name="Test",
            phone="8888888882",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH888882"
        )
        db_session.add(customer2)
        db_session.commit()

        # Second evaluation: 3 stars
        service.create_evaluate(EvaluateCreate(id_ticket=ticket2.id_ticket, star=3), customer2.id_customer)
        db_session.refresh(sample_employee)
        assert sample_employee.csat_score == 4.0  # (5+3)/2 = 4.0


# ============================================================================
# Evaluation Data Integrity Tests
# ============================================================================

class TestEvaluationDataIntegrity:
    """Tests for evaluation data validation."""

    def test_evaluation_stores_correct_ticket_id(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation stores correct ticket ID."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.id_ticket == sample_ticket_resolved.id_ticket

    def test_evaluation_stores_correct_customer_id(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation stores correct customer ID."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.id_customer == sample_customer.id_customer

    def test_evaluation_has_created_at_timestamp(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation has created_at timestamp."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.created_at is not None
        assert isinstance(evaluate.created_at, datetime)


# ============================================================================
# Edge Cases
# ============================================================================

class TestEvaluationEdgeCases:
    """Edge case tests for evaluation functionality."""

    def test_evaluation_very_long_comment(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation with very long comment."""
        service = EvaluateService(db_session)

        long_comment = "A" * 2000  # 2000 character comment

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=4,
            comment=long_comment
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert len(evaluate.comment) == 2000

    def test_evaluation_special_characters_in_comment(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test evaluation with special characters in comment."""
        service = EvaluateService(db_session)

        special_comment = "Great service! 🐱 Thanks @support #feedback"

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5,
            comment=special_comment
        )

        evaluate = service.create_evaluate(data, sample_customer.id_customer)

        assert evaluate.comment == special_comment

    def test_multiple_evaluations_same_ticket_different_customers(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        mock_notification_service
    ):
        """Test multiple evaluations for same ticket by different customers."""
        service = EvaluateService(db_session)

        # Create second customer
        customer2 = Customer(
            id=uuid4(),
            username="cust_multi",
            email="multi@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Multi",
            last_name="Customer",
            phone="9999999999",
            type="customer",
            id_customer=uuid4(),
            customer_code="KH999999"
        )
        db_session.add(customer2)
        db_session.commit()

        # Create evaluation 1
        data1 = EvaluateCreate(id_ticket=sample_ticket_resolved.id_ticket, star=5)
        service.create_evaluate(data1, sample_customer.id_customer)

        # Create evaluation 2
        data2 = EvaluateCreate(id_ticket=sample_ticket_resolved.id_ticket, star=4)
        service.create_evaluate(data2, customer2.id_customer)

        # Both should exist
        evaluates = service.get_evaluates_by_ticket(sample_ticket_resolved.id_ticket)
        assert len(evaluates) == 2

    def test_evaluation_sent_to_employee_notification(
        self,
        db_session,
        sample_ticket_resolved,
        sample_customer,
        sample_employee,
        mock_notification_service
    ):
        """Test that notification is sent to employee when evaluation is created."""
        service = EvaluateService(db_session)

        data = EvaluateCreate(
            id_ticket=sample_ticket_resolved.id_ticket,
            star=5,
            comment="Great service!"
        )

        service.create_evaluate(data, sample_customer.id_customer)

        mock_notification_service.create_and_send.assert_called()
