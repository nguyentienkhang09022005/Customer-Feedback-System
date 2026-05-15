from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.admin.systemSettingsService import SystemSettingsService
from app.schemas.admin.systemSettings import SystemSettingsUpdate, SystemSettingsOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/settings", tags=["System Settings"])


@router.get("", response_model=APIResponse[SystemSettingsOut], dependencies=[Depends(get_current_admin)])
def get_settings(db: Session = Depends(get_db)):
    settings = SystemSettingsService(db).get_settings()
    return APIResponse(status=True, code=200, message="Success", data=settings)


@router.put("", response_model=APIResponse[SystemSettingsOut], dependencies=[Depends(get_current_admin)])
def update_settings(data: SystemSettingsUpdate, db: Session = Depends(get_db)):
    try:
        settings = SystemSettingsService(db).update_settings(data)
        return APIResponse(status=True, code=200, message="Settings updated successfully", data=settings)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
