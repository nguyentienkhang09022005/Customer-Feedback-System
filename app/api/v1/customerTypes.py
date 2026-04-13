from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.services.customerTypeService import CustomerTypeService
from app.core.response import APIResponse
from app.schemas.customerTypeSchema import CustomerTypeCreate, CustomerTypeUpdate, CustomerTypeOut
from app.api.dependencies import get_current_admin

router = APIRouter(prefix="/customer-types", tags=["Customer Types Management"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("", response_model=APIResponse[List[CustomerTypeOut]])
def get_customer_types(db: Session = Depends(get_db)):
    types = CustomerTypeService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=types)

@router.post("", response_model=APIResponse[CustomerTypeOut], dependencies=[Depends(get_current_admin)])
def create_customer_type(data: CustomerTypeCreate, db: Session = Depends(get_db)):
    try:
        ctype = CustomerTypeService(db).create(data)
        return APIResponse(status=True, code=201, message="Tạo loại khách hàng thành công", data=ctype)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.put("/{type_name}", response_model=APIResponse[CustomerTypeOut], dependencies=[Depends(get_current_admin)])
def update_customer_type(type_name: str, data: CustomerTypeUpdate, db: Session = Depends(get_db)):
    try:
        ctype = CustomerTypeService(db).update(type_name, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=ctype)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{type_name}", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def delete_customer_type(type_name: str, db: Session = Depends(get_db)):
    try:
        CustomerTypeService(db).delete(type_name)
        return APIResponse(status=True, code=200, message="Xóa thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)