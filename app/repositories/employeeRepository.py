from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.human import Employee, Human
from app.models.ticket import Ticket
from typing import List, Optional


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

    # Phải check bảng Human vì Email/Phone/Username dùng chung toàn hệ thống
    def check_human_exists(self, email: str, username: str, phone: str):
        return self.db.query(Human).filter(
            (Human.email == email) |
            (Human.username == username) |
            (Human.phone == phone)
        ).first()

    def get_latest_code(self, prefix_year: str):
        return self.db.query(Employee.employee_code).filter(
            Employee.employee_code.like(f"{prefix_year}%")
        ).order_by(Employee.employee_code.desc()).first()

    def get_all(self): return self.db.query(Employee).all()

    def get_by_id(self, emp_id: str):
        return self.db.query(Employee).filter(Employee.id_employee == emp_id).first()

    def create(self, emp: Employee):
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def update(self, emp: Employee):
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def delete(self, emp: Employee):
        self.db.delete(emp)
        self.db.commit()

    def get_available_employees_by_department(self, department: str) -> List[Employee]:
        return self.db.query(Employee).filter(
            Employee.department == department,
            Employee.status == "Active"
        ).order_by(Employee.csat_score.desc()).all()

    def get_best_employee_for_assignment(self, department: str) -> Optional[Employee]:
        employees = self.get_available_employees_by_department(department)
        if not employees:
            return None
        
        active_statuses = ["New", "In Progress", "Pending", "On Hold"]
        
        for emp in employees:
            current_count = self.db.query(Ticket).filter(
                and_(
                    Ticket.id_employee == emp.id_employee,
                    Ticket.status.in_(active_statuses)
                )
            ).count()
            
            if current_count < emp.max_ticket_capacity:
                return emp
        
        return None