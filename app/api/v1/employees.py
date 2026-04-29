from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.services.employeeService import EmployeeService
from app.models.human import Employee
from app.repositories.employeeRepository import EmployeeRepository
from app.core.response import APIResponse
from app.schemas.employeeSchema import EmployeeCreate, EmployeeUpdate, EmployeeOut
from app.api.dependencies import get_db, get_current_employee, get_current_manager

router = APIRouter(prefix="/employees", tags=["Employees Management"])

@router.get("", response_model=APIResponse[List[EmployeeOut]], dependencies=[Depends(get_current_employee)])
def get_employees(db: Session = Depends(get_db)):
    emps = EmployeeService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=emps)

@router.post("", response_model=APIResponse[EmployeeOut], dependencies=[Depends(get_current_employee)])
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        emp = EmployeeService(db).create_employee(data)
        return APIResponse(status=True, code=201, message="Tạo nhân viên thành công", data=emp)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.patch("/{emp_id}", response_model=APIResponse[EmployeeOut], dependencies=[Depends(get_current_employee)])
def update_employee(emp_id: str, data: EmployeeUpdate, db: Session = Depends(get_db)):
    try:
        emp = EmployeeService(db).update_employee(emp_id, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=emp)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{emp_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_employee(emp_id: str, db: Session = Depends(get_db)):
    try:
        EmployeeService(db).delete_employee(emp_id)
        return APIResponse(status=True, code=200, message="Xóa thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/department/{dept_id}", response_model=APIResponse[List[EmployeeOut]], dependencies=[Depends(get_current_employee)])
def get_employees_by_department(dept_id: UUID, db: Session = Depends(get_db)):
    """Lấy danh sách nhân viên theo phòng ban"""
    repo = EmployeeRepository(db)
    emps = repo.get_by_department(dept_id)
    return APIResponse(status=True, code=200, message="Thành công", data=emps)

@router.get("/workload/department/{dept_id}", response_model=APIResponse)
def get_department_workload(
    dept_id: UUID,
    current_user: Employee = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Manager: xem workload của team trong phòng ban"""
    if current_user.role_name != "Admin" and current_user.id_department != dept_id:
        return APIResponse(status=False, code=403, message="Bạn chỉ có quyền xem workload trong phòng ban của mình!")

    repo = EmployeeRepository(db)
    employees = repo.get_available_employees_with_ticket_counts(dept_id)

    result = []
    for emp, count in employees:
        result.append({
            "id_employee": emp.id_employee,
            "first_name": emp.first_name,
            "last_name": emp.last_name,
            "job_title": emp.job_title,
            "csat_score": emp.csat_score,
            "max_ticket_capacity": emp.max_ticket_capacity,
            "current_ticket_count": count,
            "capacity_usage": round(count / emp.max_ticket_capacity * 100, 1) if emp.max_ticket_capacity > 0 else 0
        })

    return APIResponse(status=True, code=200, message="Thành công", data=result)

@router.patch("/manager/{emp_id}", response_model=APIResponse[EmployeeOut])
def manager_update_employee(
    emp_id: str,
    data: EmployeeUpdate,
    current_user: Employee = Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    """Manager: cập nhật thông tin nhân viên trong phòng ban"""
    try:
        emp = EmployeeService(db).manager_update_employee(emp_id, data, current_user)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=emp)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)