from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
import uuid
from app.repositories.employeeRepository import EmployeeRepository
from app.models.human import Employee
from app.schemas.employeeSchema import EmployeeCreate, EmployeeUpdate
from app.core.security import get_password_hash
from app.core.constants import HumanStatusEnum, SystemConstants


class EmployeeService:
    def __init__(self, db: Session):
        self.repo = EmployeeRepository(db)

    def _generate_code(self) -> str:
        prefix_year = f"NV{datetime.utcnow().strftime('%y')}"
        latest = self.repo.get_latest_code(prefix_year)
        new_num = int(latest[0][-3:]) + 1 if (latest and latest[0]) else 1
        return f"{prefix_year}{new_num:03d}"

    def create_employee(self, data: EmployeeCreate):
        if self.repo.check_human_exists(data.email, data.username, data.phone):
            raise HTTPException(status_code=400, detail="Thông tin liên hệ hoặc Username đã tồn tại!")

        new_emp = Employee(
            **data.dict(exclude={"password"}),
            password_hash=get_password_hash(data.password),
            status=HumanStatusEnum.ACTIVE,
            employee_code=self._generate_code(),
            max_ticket_capacity=SystemConstants.DEFAULT_MAX_TICKET_CAPACITY,
            csat_score=SystemConstants.DEFAULT_CSAT_SCORE
        )
        return self.repo.create(new_emp)

    def get_all(self):
        return self.repo.get_all()

    def update_employee(self, emp_id: str, data: EmployeeUpdate):
        emp = self.repo.get_by_id(emp_id)
        if not emp: raise HTTPException(status_code=404, detail="Không tìm thấy")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(emp, key, value)
        return self.repo.update(emp)

    def delete_employee(self, emp_id: str):
        emp = self.repo.get_by_id(emp_id)
        if not emp: raise HTTPException(status_code=404, detail="Không tìm thấy")
        self.repo.delete(emp)

    def get_department_workload(self, dept_id: uuid.UUID):
        """Lấy workload của tất cả nhân viên trong phòng ban"""
        return self.repo.get_available_employees_with_ticket_counts(dept_id)