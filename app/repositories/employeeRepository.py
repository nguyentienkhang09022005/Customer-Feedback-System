from sqlalchemy.orm import Session
from app.models.human import Employee, Human


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