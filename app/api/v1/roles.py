from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import SessionLocal
from app.services.roleService import RoleService
from app.core.response import APIResponse
from app.schemas.roleSchema import RoleCreate, RoleUpdate, RoleOut

router = APIRouter(prefix="/roles", tags=["Roles Management"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("", response_model=APIResponse[List[RoleOut]])
def get_roles(db: Session = Depends(get_db)):
    roles = RoleService(db).get_all_roles()
    return APIResponse(status=True, code=200, message="Thành công", data=roles)

@router.post("", response_model=APIResponse[RoleOut])
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    try:
        role = RoleService(db).create_role(data)
        return APIResponse(status=True, code=201, message="Tạo thành công", data=role)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.put("/{role_name}", response_model=APIResponse[RoleOut])
def update_role(role_name: str, data: RoleUpdate, db: Session = Depends(get_db)):
    try:
        role = RoleService(db).update_role(role_name, data)
        return APIResponse(status=True, code=200, message="Cập nhật thành công", data=role)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)

@router.delete("/{role_name}", response_model=APIResponse)
def delete_role(role_name: str, db: Session = Depends(get_db)):
    try:
        RoleService(db).delete_role(role_name)
        return APIResponse(status=True, code=200, message="Xóa thành công")
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)