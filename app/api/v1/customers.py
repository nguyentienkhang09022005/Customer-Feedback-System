from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.services.customerService import CustomerService
from app.core.response import APIResponse
from app.schemas.customerSchema import CustomerCreate, CustomerUpdate, CustomerOut

router = APIRouter(prefix="/customers", tags=["Customers Management"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("", response_model=APIResponse[List[CustomerOut]])
def get_customers(db: Session = Depends(get_db)):
    cus = CustomerService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=cus)

@router.post("", response_model=APIResponse[CustomerOut])
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    try:
        cus = CustomerService(db).create_customer(data)
        return APIResponse(status=True, code=201, message="Tạo khách hàng thành công", data=cus)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.patch("/{cus_id}", response_model=APIResponse[CustomerOut])
def update_customer(cus_id: str, data: CustomerUpdate, db: Session = Depends(get_db)):
    try:
        cus = CustomerService(db).update_customer(cus_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=cus)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{cus_id}", response_model=APIResponse)
def delete_customer(cus_id: str, db: Session = Depends(get_db)):
    try:
        CustomerService(db).delete_customer(cus_id)
        return APIResponse(status=True, code=200, message="Xóa thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)