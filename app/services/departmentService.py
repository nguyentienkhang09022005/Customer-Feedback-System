from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.departmentRepository import DepartmentRepository
from app.models.department import Department
from app.schemas.departmentSchema import DepartmentCreate, DepartmentUpdate
from typing import List
import uuid


class DepartmentService:
    def __init__(self, db: Session):
        self.repo = DepartmentRepository(db)

    def create_department(self, data: DepartmentCreate) -> Department:
        existing = self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="Tên phòng ban đã tồn tại!")

        new_dept = Department(**data.model_dump())
        return self.repo.create(new_dept)

    def get_all(self) -> List[Department]:
        return self.repo.get_all()

    def get_by_id(self, dept_id: uuid.UUID) -> Department:
        dept = self.repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban!")
        return dept

    def get_active_all(self) -> List[Department]:
        return self.repo.get_active_all()

    def update_department(self, dept_id: uuid.UUID, data: DepartmentUpdate) -> Department:
        dept = self.repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban!")

        if data.name and data.name != dept.name:
            existing = self.repo.get_by_name(data.name)
            if existing:
                raise HTTPException(status_code=400, detail="Tên phòng ban đã tồn tại!")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dept, key, value)

        return self.repo.update(dept)

    def delete_department(self, dept_id: uuid.UUID):
        dept = self.repo.get_by_id(dept_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Không tìm thấy phòng ban!")
        self.repo.delete(dept)
