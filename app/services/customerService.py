from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.repositories.customerRepository import CustomerRepository
from app.models.human import Customer
from app.schemas.customerSchema import CustomerCreate, CustomerUpdate
from app.core.security import get_password_hash
from app.core.constants import HumanStatusEnum, MembershipTierEnum


class CustomerService:
    def __init__(self, db: Session):
        self.repo = CustomerRepository(db)

    def _generate_code(self) -> str:
        prefix_year = f"KH{datetime.utcnow().strftime('%y')}"
        latest = self.repo.get_latest_code(prefix_year)
        new_num = int(latest[0][-3:]) + 1 if (latest and latest[0]) else 1
        return f"{prefix_year}{new_num:03d}"

    def create_customer(self, data: CustomerCreate):
        if self.repo.check_human_exists(data.email, data.username, data.phone):
            raise HTTPException(status_code=400, detail="Thông tin liên hệ hoặc Username đã tồn tại!")

        new_cus = Customer(
            **data.dict(exclude={"password"}),
            password_hash=get_password_hash(data.password),
            status=HumanStatusEnum.ACTIVE,
            customer_code=self._generate_code(),
            membership_tier=MembershipTierEnum.STANDARD
        )
        return self.repo.create(new_cus)

    def get_all(self):
        return self.repo.get_all()

    def update_customer(self, cus_id: str, data: CustomerUpdate):
        cus = self.repo.get_by_id(cus_id)
        if not cus:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")

        update_data = data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(cus, key, value)

        return self.repo.update(cus)

    def delete_customer(self, cus_id: str):
        cus = self.repo.get_by_id(cus_id)
        if not cus:
            raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
        self.repo.delete(cus)