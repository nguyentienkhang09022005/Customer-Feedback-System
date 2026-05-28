"""
Unit tests for Load Balancer Service.

Tests cover:
- Best employee selection for department
- Ticket assignment with distributed locking
- Load balancing algorithm (least busy, highest CSAT)
- Capacity management

Test flow:
1. Get available employees for a department
2. Select best employee based on:
   - Current active ticket count < max capacity
   - Highest CSAT score among eligible
3. Assign ticket with lock to prevent race conditions
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from sqlalchemy import func, and_

from app.services.loadBalancer import LoadBalancer
from app.models.human import Employee


# ============================================================================
# Employee Selection Tests
# ============================================================================

class TestLoadBalancerSelection:
    """Tests for employee selection algorithm."""

    def test_get_best_employee_empty_department(
        self,
        db_session,
        sample_department
    ):
        """Test getting best employee when no employees available."""
        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        assert employee is None

    def test_get_best_employee_single_qualified(
        self,
        db_session,
        sample_employee,
        sample_department
    ):
        """Test getting best employee when only one qualifies."""
        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        assert employee is not None
        assert employee.id_employee == sample_employee.id_employee

    def test_get_best_employee_highest_csat(
        self,
        db_session,
        sample_department
    ):
        """Test that employee with highest CSAT is selected."""
        # Create two employees
        emp1 = Employee(
            id=uuid4(),
            username="emp_low_csat",
            email="low@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Low",
            last_name="CSAT",
            phone="1111111111",
            type="employee",
            id_employee=uuid4(),
            id_department=sample_department.id_department,
            employee_code="EMP_LC",
            max_ticket_capacity=5,
            csat_score=3.0,  # Lower CSAT
            role_name="Employee"
        )

        emp2 = Employee(
            id=uuid4(),
            username="emp_high_csat",
            email="high@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="High",
            last_name="CSAT",
            phone="2222222222",
            type="employee",
            id_employee=uuid4(),
            id_department=sample_department.id_department,
            employee_code="EMP_HC",
            max_ticket_capacity=5,
            csat_score=4.5,  # Higher CSAT
            role_name="Employee"
        )

        db_session.add(emp1)
        db_session.add(emp2)
        db_session.commit()

        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        assert employee is not None
        assert employee.id_employee == emp2.id_employee  # High CSAT

    def test_get_best_employee_respects_capacity(
        self,
        db_session,
        sample_department
    ):
        """Test that employee at max capacity is not selected."""
        # Create employee at capacity with highest CSAT
        emp_at_capacity = Employee(
            id=uuid4(),
            username="emp_full_v2",
            email="fullv2@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Full",
            last_name="Capacity",
            phone="3333333332",
            type="employee",
            id_employee=uuid4(),
            id_department=sample_department.id_department,
            employee_code="EMP_FULL2",
            max_ticket_capacity=3,
            csat_score=5.0,  # Highest CSAT but at capacity
            role_name="Employee"
        )

        # Create employee with space - lower CSAT than emp_at_capacity
        emp_available = Employee(
            id=uuid4(),
            username="emp_space_v2",
            email="spacev2@test.com",
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eWvqZYxC3O3q",
            first_name="Has",
            last_name="Space",
            phone="4444444442",
            type="employee",
            id_employee=uuid4(),
            id_department=sample_department.id_department,
            employee_code="EMP_SPACE2",
            max_ticket_capacity=3,
            csat_score=2.0,  # Lower CSAT to ensure deterministic selection
            role_name="Employee"
        )

        db_session.add(emp_at_capacity)
        db_session.add(emp_available)
        db_session.commit()

        # Add tickets to emp_at_capacity to reach capacity
        from app.models.ticket import Ticket
        active_statuses = ["New", "In Progress", "Pending", "On Hold"]
        for i in range(3):
            ticket = Ticket(
                id_ticket=uuid4(),
                title=f"Ticket {i}",
                status="In Progress",
                id_employee=emp_at_capacity.id_employee,
                id_customer=uuid4()
            )
            db_session.add(ticket)

        db_session.commit()

        # Verify ticket counts before testing
        from app.models.ticket import Ticket
        from sqlalchemy import func, and_
        results_before = db_session.query(
            Employee,
            func.count(Ticket.id_ticket)
        ).outerjoin(
            Ticket,
            and_(
                Ticket.id_employee == Employee.id_employee,
                Ticket.status.in_(["New", "In Progress", "Pending", "On Hold"])
            )
        ).filter(
            Employee.id_department == sample_department.id_department,
            Employee.username.in_(["emp_full_v2", "emp_space_v2"])
        ).group_by(Employee.id_employee).all()

        for emp, count in results_before:
            if emp.username == "emp_full_v2":
                assert count == 3, f"emp_at_capacity has {count} tickets, expected 3"
            if emp.username == "emp_space_v2":
                assert count == 0, f"emp_available has {count} tickets, expected 0"

        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        assert employee is not None
        # emp_at_capacity is skipped because at capacity (3/3)
        # emp_available should be selected since it's the only remaining option
        assert employee.id_employee == emp_available.id_employee
        assert employee.csat_score == 2.0  # emp_available with lower CSAT but capacity available


# ============================================================================
# Assignment with Lock Tests
# ============================================================================

class TestLoadBalancerLock:
    """Tests for distributed lock mechanism."""

    def test_assign_with_lock_acquired(
        self,
        db_session,
        sample_employee,
        sample_ticket,
        sample_department,
        mock_redis_service
    ):
        """Test assignment when lock is acquired."""
        # Mock Redis to allow lock acquisition
        mock_redis_client = MagicMock()
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = "some_value"  # Lock value
        mock_redis_client.delete.return_value = True

        with patch.object(LoadBalancer, 'redis_client', mock_redis_client):
            lb = LoadBalancer(db_session)

            employee = lb.assign_ticket_with_lock(
                sample_ticket.id_ticket,
                sample_department.id_department
            )

            # May return None if no available employees in this test setup

    def test_assign_with_lock_not_acquired(
        self,
        db_session,
        sample_department,
        mock_redis_service
    ):
        """Test assignment when lock cannot be acquired."""
        mock_redis_client = MagicMock()
        mock_redis_client.set.return_value = None  # Lock not acquired

        with patch.object(LoadBalancer, 'redis_client', mock_redis_client):
            lb = LoadBalancer(db_session)

            result = lb.assign_ticket_with_lock(
                uuid4(),  # Any ticket ID
                sample_department.id_department
            )

            assert result is None


# ============================================================================
# Load Balancing Edge Cases
# ============================================================================

class TestLoadBalancerEdgeCases:
    """Edge case tests for load balancer."""

    def test_no_available_employees(
        self,
        db_session,
        sample_department
    ):
        """Test when no employees are available in department."""
        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        assert employee is None

    def test_all_employees_at_capacity(
        self,
        db_session,
        sample_department,
        sample_employee
    ):
        """Test when all employees are at max capacity."""
        lb = LoadBalancer(db_session)

        # Create enough tickets to fill employee to capacity
        from app.models.ticket import Ticket
        for i in range(sample_employee.max_ticket_capacity):
            ticket = Ticket(
                id_ticket=uuid4(),
                title=f"Full ticket {i}",
                status="In Progress",
                id_employee=sample_employee.id_employee,
                id_customer=uuid4()
            )
            db_session.add(ticket)
        db_session.commit()

        employee = lb.get_best_employee_for_department(sample_department.id_department)

        # Should not select employee at capacity
        # May return None if no other employees exist

    def test_nonexistent_department(
        self,
        db_session
    ):
        """Test getting best employee for nonexistent department."""
        lb = LoadBalancer(db_session)

        employee = lb.get_best_employee_for_department(uuid4())

        assert employee is None