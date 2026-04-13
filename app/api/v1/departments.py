from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.departmentService import DepartmentService
from app.schemas.departmentSchema import DepartmentCreate, DepartmentUpdate, DepartmentOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee
from app.services.chatbotService import ChatbotService

router = APIRouter(prefix="/departments", tags=["Department Management"])


@router.get("", response_model=APIResponse[List[DepartmentOut]], dependencies=[Depends(get_current_employee)])
def get_departments(db: Session = Depends(get_db)):
    departments = DepartmentService(db).get_all()
    return APIResponse(status=True, code=200, message="Thành công", data=departments)


@router.post("", response_model=APIResponse[DepartmentOut], dependencies=[Depends(get_current_employee)])
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    try:
        dept = DepartmentService(db).create_department(data)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=201, message="Tạo phòng ban thành công", data=dept)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.get("/{dept_id}", response_model=APIResponse[DepartmentOut], dependencies=[Depends(get_current_employee)])
def get_department(dept_id: UUID, db: Session = Depends(get_db)):
    try:
        dept = DepartmentService(db).get_by_id(dept_id)
        return APIResponse(status=True, code=200, message="Thành công", data=dept)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.patch("/{dept_id}", response_model=APIResponse[DepartmentOut], dependencies=[Depends(get_current_employee)])
def update_department(dept_id: UUID, data: DepartmentUpdate, db: Session = Depends(get_db)):
    try:
        dept = DepartmentService(db).update_department(dept_id, data)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=dept)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.delete("/{dept_id}", response_model=APIResponse, dependencies=[Depends(get_current_employee)])
def delete_department(dept_id: UUID, db: Session = Depends(get_db)):
    try:
        DepartmentService(db).delete_department(dept_id)
        ChatbotService.invalidate_public_data_cache()
        return APIResponse(status=True, code=200, message="Xóa phòng ban thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
