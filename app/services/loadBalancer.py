from sqlalchemy.orm import Session
from app.repositories.employeeRepository import EmployeeRepository
from app.repositories.ticketRepository import TicketRepository
from app.models.human import Employee
from typing import Optional


class LoadBalancer:
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.ticket_repo = TicketRepository(db)

    def get_best_employee_for_department(self, department: str) -> Optional[Employee]:
        employees = self.employee_repo.get_available_employees_by_department(department)
        
        if not employees:
            return None
        
        best_employee = None
        best_csat = -1
        
        for emp in employees:
            current_count = self.ticket_repo.get_active_ticket_count(emp.id_employee)
            if current_count < emp.max_ticket_capacity:
                if emp.csat_score > best_csat:
                    best_csat = emp.csat_score
                    best_employee = emp
        
        return best_employee
