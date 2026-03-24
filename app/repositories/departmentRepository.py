from sqlalchemy.orm import Session
from app.models.department import Department
from typing import List, Optional
import uuid


class DepartmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Department]:
        return self.db.query(Department).all()

    def get_by_id(self, dept_id: uuid.UUID) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id_department == dept_id).first()

    def get_by_name(self, name: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.name == name).first()

    def get_active_all(self) -> List[Department]:
        return self.db.query(Department).filter(Department.is_active == True).all()

    def create(self, department: Department) -> Department:
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def update(self, department: Department) -> Department:
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete(self, department: Department):
        self.db.delete(department)
        self.db.commit()
