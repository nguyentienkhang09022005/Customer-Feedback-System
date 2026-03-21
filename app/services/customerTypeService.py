from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.customerTypeRepository import CustomerTypeRepository
from app.models.human import CustomerType
from app.schemas.customerTypeSchema import CustomerTypeCreate, CustomerTypeUpdate


class CustomerTypeService:
    def __init__(self, db: Session):
        self.repo = CustomerTypeRepository(db)

    def get_all(self):
        return self.repo.get_all()

    def create(self, data: CustomerTypeCreate):
        if self.repo.get_by_name(data.type_name):
            raise HTTPException(status_code=400, detail="Loại khách hàng này đã tồn tại")
        return self.repo.create(CustomerType(**data.dict()))

    def update(self, type_name: str, data: CustomerTypeUpdate):
        ctype = self.repo.get_by_name(type_name)
        if not ctype: raise HTTPException(status_code=404, detail="Không tìm thấy")

        for key, value in data.dict(exclude_unset=True).items():
            setattr(ctype, key, value)
        return self.repo.update(ctype)

    def delete(self, type_name: str):
        ctype = self.repo.get_by_name(type_name)
        if not ctype: raise HTTPException(status_code=404, detail="Không tìm thấy")
        self.repo.delete(ctype)