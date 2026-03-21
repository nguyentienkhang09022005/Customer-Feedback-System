from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.services.employeeService import EmployeeService
from app.core.response import APIResponse
from app.schemas.employeeSchema import EmployeeCreate, EmployeeUpdate, EmployeeOut

router = APIRouter(prefix="/employees", tags=["Employees Management"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("", response_model=APIResponse[List[EmployeeOut]])
def get_employees(db: Session = Depends(get_db)):
    emps = EmployeeService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=emps)

@router.post("", response_model=APIResponse[EmployeeOut])
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        emp = EmployeeService(db).create_employee(data)
        return APIResponse(status=True, code=201, message="Tạo nhân viên thành công", data=emp)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.patch("/{emp_id}", response_model=APIResponse[EmployeeOut])
def update_employee(emp_id: str, data: EmployeeUpdate, db: Session = Depends(get_db)):
    try:
        emp = EmployeeService(db).update_employee(emp_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=emp)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{emp_id}", response_model=APIResponse)
def delete_employee(emp_id: str, db: Session = Depends(get_db)):
    try:
        EmployeeService(db).delete_employee(emp_id)
        return APIResponse(status=True, code=200, message="Xóa thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)