from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.services.notificationService import NotificationService
from app.schemas.notificationSchema import NotificationOut
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_user
from app.models.human import Human

router = APIRouter(prefix="/notifications", tags=["Notification Management"])

@router.get("", response_model=APIResponse[List[NotificationOut]])
def get_my_notifications(
    is_unread_only: bool = False,
    skip: int = 0,
    limit: int = 20,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NotificationService(db)
    notis = service.get_my_notifications(current_user.id, is_unread_only, skip, limit)
    return APIResponse(status=True, code=200, message="Lấy danh sách thành công!", data=notis)

@router.patch("/{notification_id}/read", response_model=APIResponse[NotificationOut])
def mark_notification_read(
    notification_id: UUID,
    current_user: Human = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = NotificationService(db)
        noti = service.mark_as_read(notification_id, current_user.id)
        return APIResponse(status=True, code=200, message="Đã đọc thông báo!", data=noti)
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)