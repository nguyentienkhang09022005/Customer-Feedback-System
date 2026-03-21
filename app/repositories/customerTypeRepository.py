from sqlalchemy.orm import Session
from app.models.human import CustomerType


class CustomerTypeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self): return self.db.query(CustomerType).all()

    def get_by_name(self, type_name: str):
        return self.db.query(CustomerType).filter(CustomerType.type_name == type_name).first()

    def create(self, ctype: CustomerType):
        self.db.add(ctype)
        self.db.commit()
        self.db.refresh(ctype)
        return ctype

    def update(self, ctype: CustomerType):
        self.db.commit()
        self.db.refresh(ctype)
        return ctype

    def delete(self, ctype: CustomerType):
        self.db.delete(ctype)
        self.db.commit()