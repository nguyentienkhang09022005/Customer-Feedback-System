from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class DepartmentAssignmentRequest(BaseModel):
    """Yêu cầu gán nhân viên vào phòng ban"""
    employee_id: UUID
    department_id: UUID


class DepartmentTransferRequest(BaseModel):
    """Yêu cầu chuyển nhân viên sang phòng ban khác"""
    employee_id: UUID
    new_department_id: UUID


class DepartmentUnassignRequest(BaseModel):
    """Yêu cầu xóa nhân viên khỏi phòng ban (không xóa nhân viên)"""
    employee_id: UUID


class SetManagerRequest(BaseModel):
    """Yêu cầu chỉ định Manager cho phòng ban"""
    employee_id: UUID
    department_id: UUID


class EmployeeAssignmentOut(BaseModel):
    """Thông tin phân bổ phòng ban của nhân viên"""
    employee_id: UUID
    employee_code: Optional[str] = None
    full_name: str
    job_title: Optional[str] = None
    role_name: Optional[str] = None
    department_id: Optional[UUID] = None
    department_name: Optional[str] = None
    is_manager: bool = False

    class Config:
        from_attributes = True


class DepartmentMemberOut(BaseModel):
    """Thông tin thành viên trong phòng ban"""
    employee_id: UUID
    employee_code: Optional[str] = None
    full_name: str
    job_title: Optional[str] = None
    role_name: Optional[str] = None
    is_manager: bool = False

    class Config:
        from_attributes = True


class DepartmentWithMembersOut(BaseModel):
    """Thông tin phòng ban kèm danh sách thành viên"""
    id_department: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    manager: Optional[DepartmentMemberOut] = None
    members: list[DepartmentMemberOut] = []

    class Config:
        from_attributes = True
