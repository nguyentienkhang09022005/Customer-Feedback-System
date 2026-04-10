from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.departmentAssignmentService import DepartmentAssignmentService
from app.schemas.departmentAssignmentSchema import (
    DepartmentAssignmentRequest,
    DepartmentTransferRequest,
    DepartmentUnassignRequest,
    SetManagerRequest,
    EmployeeAssignmentOut,
    DepartmentWithMembersOut,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/department-assignments", tags=["Department Assignment Management"])


@router.get("", response_model=APIResponse[List[EmployeeAssignmentOut]], dependencies=[Depends(get_current_admin)])
def get_all_assignments(db: Session = Depends(get_db)):
    """Lấy tất cả phân bổ phòng ban - Admin only"""
    service = DepartmentAssignmentService(db)
    assignments = service.get_all_department_assignments()
    return APIResponse(status=True, code=200, message="Thành công", data=assignments)


@router.get("/employees/{emp_id}", response_model=APIResponse[EmployeeAssignmentOut], dependencies=[Depends(get_current_admin)])
def get_employee_assignment(emp_id: UUID, db: Session = Depends(get_db)):
    """Lấy thông tin phân bổ của nhân viên - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        assignment = service.get_employee_assignment(str(emp_id))
        return APIResponse(status=True, code=200, message="Thành công", data=assignment)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/departments/{dept_id}/members", response_model=APIResponse[DepartmentWithMembersOut], dependencies=[Depends(get_current_admin)])
def get_department_members(dept_id: UUID, db: Session = Depends(get_db)):
    """Lấy thông tin phòng ban kèm danh sách thành viên - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        dept_with_members = service.get_department_with_members(str(dept_id))
        return APIResponse(status=True, code=200, message="Thành công", data=dept_with_members)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("", response_model=APIResponse[EmployeeAssignmentOut], dependencies=[Depends(get_current_admin)])
def assign_employee_to_department(data: DepartmentAssignmentRequest, db: Session = Depends(get_db)):
    """Gán nhân viên vào phòng ban - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        result = service.assign_employee_to_department(data)
        return APIResponse(status=True, code=201, message="Gán nhân viên vào phòng ban thành công", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/transfer", response_model=APIResponse[EmployeeAssignmentOut], dependencies=[Depends(get_current_admin)])
def transfer_employee_to_department(data: DepartmentTransferRequest, db: Session = Depends(get_db)):
    """Chuyển nhân viên sang phòng ban khác - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        result = service.transfer_employee_to_department(data)
        return APIResponse(status=True, code=200, message="Chuyển phòng ban thành công", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/manager", response_model=APIResponse[EmployeeAssignmentOut], dependencies=[Depends(get_current_admin)])
def set_department_manager(data: SetManagerRequest, db: Session = Depends(get_db)):
    """Chỉ định Manager cho phòng ban - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        result = service.set_department_manager(data)
        return APIResponse(status=True, code=200, message="Chỉ định Manager thành công", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("", response_model=APIResponse[EmployeeAssignmentOut], dependencies=[Depends(get_current_admin)])
def remove_employee_from_department(data: DepartmentUnassignRequest, db: Session = Depends(get_db)):
    """Xóa nhân viên khỏi phòng ban - Admin only"""
    try:
        service = DepartmentAssignmentService(db)
        result = service.remove_employee_from_department(data)
        return APIResponse(status=True, code=200, message="Xóa nhân viên khỏi phòng ban thành công", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
