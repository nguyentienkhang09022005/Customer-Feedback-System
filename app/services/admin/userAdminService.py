from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.employeeRepository import EmployeeRepository
from app.repositories.customerRepository import CustomerRepository
from app.core.security import get_password_hash
from app.core.constants import HumanStatusEnum


class UserAdminService:
    def __init__(self, db: Session):
        self.db = db
        self.employee_repo = EmployeeRepository(db)
        self.customer_repo = CustomerRepository(db)

    def _get_employee_or_404(self, emp_id: str):
        emp = self.employee_repo.get_by_id(emp_id)
        if not emp:
            raise HTTPException(status_code=404, detail="Employee not found")
        return emp

    def _get_customer_or_404(self, cus_id: str):
        cus = self.customer_repo.get_by_id(cus_id)
        if not cus:
            raise HTTPException(status_code=404, detail="Customer not found")
        return cus

    def update_user_status(self, user_type: str, user_id: str, status: str) -> dict:
        # Validate status value against HumanStatusEnum
        valid_statuses = [s.value for s in HumanStatusEnum]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        if user_type == "employee":
            user = self._get_employee_or_404(user_id)
            user.status = status
            self.employee_repo.update(user)
        elif user_type == "customer":
            user = self._get_customer_or_404(user_id)
            user.status = status
            self.customer_repo.update(user)
        else:
            raise HTTPException(status_code=400, detail="Invalid user_type")

        return {"user_type": user_type, "user_id": user_id, "status": status}

    def reset_password(self, user_type: str, user_id: str, new_password: str) -> dict:
        if not new_password or len(new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters"
            )

        if user_type == "employee":
            user = self._get_employee_or_404(user_id)
            user.password_hash = get_password_hash(new_password)
            self.employee_repo.update(user)
        elif user_type == "customer":
            user = self._get_customer_or_404(user_id)
            user.password_hash = get_password_hash(new_password)
            self.customer_repo.update(user)
        else:
            raise HTTPException(status_code=400, detail="Invalid user_type")

        return {"user_type": user_type, "user_id": user_id, "message": "Password reset successfully"}
