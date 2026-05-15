from sqlalchemy.orm import Session
from app.repositories.employeeRepository import EmployeeRepository
from app.repositories.ticketRepository import TicketRepository
from app.models.department import Department
from app.schemas.admin.workloadReport import (
    SystemWideWorkloadItem,
    SystemWideWorkloadResponse,
    DepartmentSummaryItem,
    DepartmentSummaryResponse,
)


class WorkloadReportService:
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.ticket_repo = TicketRepository(db)

    def get_system_wide_workload(self) -> SystemWideWorkloadResponse:
        """
        Get system-wide workload report for all employees.
        Returns employee_id, name, department, job_title, open_tickets,
        max_capacity, utilization %, csat_score.
        """
        employees = self.employee_repo.get_all()
        employee_items = []
        total_open_tickets = 0

        for emp in employees:
            open_tickets = self.ticket_repo.get_active_ticket_count(emp.id_employee)
            max_capacity = emp.max_ticket_capacity or 1
            utilization = (open_tickets / max_capacity * 100) if max_capacity > 0 else 0.0

            name = f"{emp.first_name} {emp.last_name}".strip() if emp.first_name or emp.last_name else emp.username

            department_name = None
            if emp.id_department:
                dept = self.db.query(Department).filter(Department.id_department == emp.id_department).first()
                if dept:
                    department_name = dept.name

            employee_items.append(SystemWideWorkloadItem(
                employee_id=emp.id_employee,
                name=name,
                department=department_name,
                job_title=emp.job_title,
                open_tickets=open_tickets,
                max_capacity=max_capacity,
                utilization_percent=round(utilization, 2),
                csat_score=round(emp.csat_score or 0.0, 2)
            ))
            total_open_tickets += open_tickets

        total_employees = len(employee_items)
        overall_utilization = 0.0
        if total_employees > 0:
            total_capacity = sum(item.max_capacity for item in employee_items)
            overall_utilization = (total_open_tickets / total_capacity * 100) if total_capacity > 0 else 0.0

        return SystemWideWorkloadResponse(
            employees=employee_items,
            total_employees=total_employees,
            total_open_tickets=total_open_tickets,
            overall_utilization_percent=round(overall_utilization, 2)
        )

    def get_department_summary(self) -> DepartmentSummaryResponse:
        """
        Get department summary workload report.
        Returns department_id, department_name, member_count, total_capacity,
        total_load, utilization %.
        """
        departments = self.db.query(Department).filter(Department.is_active == True).all()
        department_items = []

        for dept in departments:
            members = self.employee_repo.get_by_department(dept.id_department)
            member_count = len(members)

            total_capacity = sum(emp.max_ticket_capacity or 0 for emp in members)
            total_load = 0

            for emp in members:
                load = self.ticket_repo.get_active_ticket_count(emp.id_employee)
                total_load += load

            utilization = (total_load / total_capacity * 100) if total_capacity > 0 else 0.0

            department_items.append(DepartmentSummaryItem(
                department_id=dept.id_department,
                department_name=dept.name,
                member_count=member_count,
                total_capacity=total_capacity,
                total_load=total_load,
                utilization_percent=round(utilization, 2)
            ))

        return DepartmentSummaryResponse(
            departments=department_items,
            total_departments=len(department_items)
        )