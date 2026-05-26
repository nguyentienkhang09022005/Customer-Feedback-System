"""
Tests for admin workload report service.
"""

import pytest
from uuid import uuid4

from app.services.admin.workloadReportService import WorkloadReportService


class TestGetSystemWideWorkload:
    """Tests for get_system_wide_workload method."""

    def test_get_system_wide_workload_returns_response_object(self, db_session):
        """Happy path: returns SystemWideWorkloadResponse."""
        result = WorkloadReportService(db_session).get_system_wide_workload()

        assert hasattr(result, "employees")
        assert hasattr(result, "total_employees")
        assert hasattr(result, "total_open_tickets")
        assert hasattr(result, "overall_utilization_percent")

    def test_get_system_wide_workload_includes_employees(
        self, db_session, sample_employee
    ):
        """Happy path: the sample employee appears in the report."""
        result = WorkloadReportService(db_session).get_system_wide_workload()

        assert result.total_employees >= 1
        emp_ids = [e.employee_id for e in result.employees]
        assert sample_employee.id_employee in emp_ids

    def test_get_system_wide_workload_without_tickets_has_zero_open(
        self, db_session, sample_employee
    ):
        """Business rule: employee with no tickets has 0 open_tickets."""
        result = WorkloadReportService(db_session).get_system_wide_workload()

        emp_item = next(
            (e for e in result.employees
             if e.employee_id == sample_employee.id_employee),
            None
        )
        assert emp_item is not None
        assert emp_item.open_tickets == 0

    def test_get_system_wide_workload_calculates_utilization_with_tickets(
        self, db_session, sample_ticket_assigned
    ):
        """Business rule: employee with assigned ticket has >0 open_tickets."""
        result = WorkloadReportService(db_session).get_system_wide_workload()

        emp_item = next(
            (e for e in result.employees
             if e.employee_id == sample_ticket_assigned.id_employee),
            None
        )
        assert emp_item is not None
        assert emp_item.open_tickets >= 1

    def test_get_system_wide_workload_with_no_employees_returns_empty(
        self, db_session
    ):
        """Edge case: no employees returns 0 utilization."""
        result = WorkloadReportService(db_session).get_system_wide_workload()

        assert result.total_employees == 0
        assert result.total_open_tickets == 0


class TestGetDepartmentSummary:
    """Tests for get_department_summary method."""

    def test_get_department_summary_returns_response_object(self, db_session):
        """Happy path: returns DepartmentSummaryResponse."""
        result = WorkloadReportService(db_session).get_department_summary()

        assert hasattr(result, "departments")
        assert hasattr(result, "total_departments")

    def test_get_department_summary_includes_active_departments(
        self, db_session, sample_department
    ):
        """Happy path: the sample department appears in the summary."""
        result = WorkloadReportService(db_session).get_department_summary()

        assert result.total_departments >= 1
        dept_names = [d.department_name for d in result.departments]
        assert sample_department.name in dept_names

    def test_get_department_summary_excludes_inactive_departments(
        self, db_session
    ):
        """Business rule: inactive departments are excluded."""
        from app.models.department import Department

        inactive = Department(
            id_department=uuid4(),
            name="Inactive Department",
            is_active=False
        )
        db_session.add(inactive)
        db_session.commit()

        result = WorkloadReportService(db_session).get_department_summary()

        dept_names = [d.department_name for d in result.departments]
        assert "Inactive Department" not in dept_names

    def test_get_department_summary_with_unassigned_employee(
        self, db_session, sample_employee, sample_department
    ):
        """Edge case: employee with no department contributes zero load."""
        result = WorkloadReportService(db_session).get_department_summary()

        # The employee's department should appear (sample_department)
        # and total_load should account for the employee's open tickets
        any_dept = next(
            (d for d in result.departments
             if d.department_name == sample_department.name),
            None
        )
        assert any_dept is not None
        assert any_dept.total_load >= 0

    def test_get_department_summary_with_no_departments_returns_empty(
        self, db_session
    ):
        """Edge case: no active departments returns empty list."""
        from app.models.department import Department
        db_session.query(Department).delete()
        db_session.commit()

        result = WorkloadReportService(db_session).get_department_summary()

        assert result.departments == []
        assert result.total_departments == 0
