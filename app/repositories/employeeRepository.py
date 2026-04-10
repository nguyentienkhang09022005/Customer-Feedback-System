from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.human import Employee, Human
from app.models.ticket import Ticket
from typing import List, Optional
import uuid


class EmployeeRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def get_by_department(self, dept_id: uuid.UUID) -> List[Employee]:
        return self.db.query(Employee).filter(Employee.id_department == dept_id).all()

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

    def get_available_employees_by_department(self, dept_id: uuid.UUID) -> List[Employee]:
        return self.db.query(Employee).filter(
            Employee.id_department == dept_id,
            Employee.status == "Active"
        ).order_by(Employee.csat_score.desc()).all()

    def get_available_employees_with_ticket_counts(self, dept_id: uuid.UUID):
        """Lấy danh sách employees kèm số ticket đang active trong 1 query"""
        active_statuses = ["New", "In Progress", "Pending", "On Hold"]
        
        results = self.db.query(
            Employee,
            func.coalesce(func.count(Ticket.id_ticket), 0).label('ticket_count')
        ).outerjoin(
            Ticket,
            and_(
                Ticket.id_employee == Employee.id_employee,
                Ticket.status.in_(active_statuses)
            )
        ).filter(
            Employee.id_department == dept_id,
            Employee.status == "Active"
        ).group_by(Employee.id_employee).order_by(
            Employee.csat_score.desc()
        ).all()
        
        return results

    def get_best_employee_for_assignment(self, dept_id: uuid.UUID) -> Optional[Employee]:
        employees = self.get_available_employees_by_department(dept_id)
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

    def assign_to_department(self, emp_id: uuid.UUID, dept_id: uuid.UUID) -> Employee:
        """Gán nhân viên vào phòng ban"""
        emp = self.get_by_id(str(emp_id))
        if emp:
            emp.id_department = dept_id
            self.db.commit()
            self.db.refresh(emp)
        return emp

    def remove_from_department(self, emp_id: uuid.UUID) -> Employee:
        """Xóa nhân viên khỏi phòng ban (set id_department = None)"""
        emp = self.get_by_id(str(emp_id))
        if emp:
            emp.id_department = None
            self.db.commit()
            self.db.refresh(emp)
        return emp

    def get_department_manager(self, dept_id: uuid.UUID) -> Optional[Employee]:
        """Lấy manager của phòng ban"""
        return self.db.query(Employee).filter(
            Employee.id_department == dept_id,
            Employee.role_name == "Manager"
        ).first()

    def get_department_members(self, dept_id: uuid.UUID) -> List[Employee]:
        """Lấy tất cả thành viên trong phòng ban (không bao gồm manager đã được chỉ định riêng)"""
        return self.db.query(Employee).filter(
            Employee.id_department == dept_id,
            Employee.role_name != "Manager"
        ).all()

    def get_department_all_members(self, dept_id: uuid.UUID) -> List[Employee]:
        """Lấy tất cả thành viên trong phòng ban (bao gồm cả manager)"""
        return self.db.query(Employee).filter(
            Employee.id_department == dept_id
        ).all()