from sqlalchemy.orm import Session
from app.models.human import Customer, Human


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    # Check bảng Human chung vì hệ thống không cho phép trùng email/phone/username dù là ai
    def check_human_exists(self, email: str, username: str, phone: str):
        return self.db.query(Human).filter(
            (Human.email == email) |
            (Human.username == username) |
            (Human.phone == phone)
        ).first()

    def get_latest_code(self, prefix_year: str):
        return self.db.query(Customer.customer_code).filter(
            Customer.customer_code.like(f"{prefix_year}%")
        ).order_by(Customer.customer_code.desc()).first()

    def get_all(self):
        return self.db.query(Customer).all()

    def get_by_id(self, cus_id: str):
        return self.db.query(Customer).filter(Customer.id_customer == cus_id).first()

    def create(self, cus: Customer):
        self.db.add(cus)
        self.db.commit()
        self.db.refresh(cus)
        return cus

    def update(self, cus: Customer):
        self.db.commit()
        self.db.refresh(cus)
        return cus

    def delete(self, cus: Customer):
        self.db.delete(cus)
        self.db.commit()