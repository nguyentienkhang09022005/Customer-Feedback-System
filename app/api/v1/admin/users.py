from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.admin.userAdminService import UserAdminService
from app.schemas.admin.userAdmin import UserStatusUpdate, PasswordResetRequest
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/users", tags=["Admin User Management"])


@router.post("/status", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def update_user_status(data: UserStatusUpdate, db: Session = Depends(get_db)):
    try:
        result = UserAdminService(db).update_user_status(
            user_type=data.user_type,
            user_id=str(data.user_id),
            status=data.status
        )
        return APIResponse(status=True, code=200, message="User status updated successfully", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)


@router.post("/reset-password", response_model=APIResponse, dependencies=[Depends(get_current_admin)])
def reset_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    try:
        result = UserAdminService(db).reset_password(
            user_type=data.user_type,
            user_id=str(data.user_id),
            new_password=data.new_password
        )
        return APIResponse(status=True, code=200, message="Password reset successfully", data=result)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
