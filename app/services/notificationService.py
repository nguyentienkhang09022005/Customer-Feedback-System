from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.notificationRepository import NotificationRepository
from app.models.interaction import Notification
from app.schemas.notificationSchema import NotificationCreate, NotificationOut
from typing import List
import uuid
import asyncio

# Import socket manager của bạn
from app.socketio.manager import sio, chat_namespace


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificationRepository(db)

    def create_and_send(self, data: NotificationCreate) -> Notification:
        notification = Notification(
            title=data.title,
            content=data.content,
            notification_type=data.notification_type,
            id_reference=data.id_reference,
            id_receiver=data.id_receiver
        )
        created_noti = self.repo.create(notification)

        self._emit_realtime_notification(created_noti)

        return created_noti

    def get_my_notifications(self, user_id: uuid.UUID, is_unread_only: bool = False, skip: int = 0, limit: int = 20) -> \
    List[Notification]:
        if is_unread_only:
            return self.repo.get_unread_user_notifications(user_id, skip, limit)
        return self.repo.get_user_notifications(user_id, skip, limit)

    def mark_as_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification:
        notification = self.repo.get_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông báo!")

        if notification.id_receiver != user_id:
            raise HTTPException(status_code=403, detail="Bạn không có quyền thao tác thông báo này!")

        return self.repo.mark_as_read(notification)

    def _emit_realtime_notification(self, notification: Notification):
        room = f"user_{notification.id_receiver}"
        noti_data = {
            "id_notification": str(notification.id_notification),
            "title": notification.title,
            "content": notification.content,
            "notification_type": notification.notification_type,
            "created_at": notification.created_at.isoformat(),
            "id_reference": str(notification.id_reference) if notification.id_reference else None
        }

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(sio.emit('new_notification', noti_data, room=room, namespace=chat_namespace))
        except RuntimeError:
            asyncio.run(sio.emit('new_notification', noti_data, room=room, namespace=chat_namespace))