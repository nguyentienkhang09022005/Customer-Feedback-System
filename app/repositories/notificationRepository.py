from sqlalchemy.orm import Session
from app.models.interaction import Notification
from typing import List
import uuid

class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_id(self, notification_id: uuid.UUID) -> Notification:
        return self.db.query(Notification).filter(Notification.id_notification == notification_id).first()

    def get_user_notifications(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> List[Notification]:
        return self.db.query(Notification)\
            .filter(Notification.id_receiver == user_id)\
            .order_by(Notification.created_at.desc())\
            .offset(skip).limit(limit).all()

    def get_unread_user_notifications(self, user_id: uuid.UUID, skip: int = 0, limit: int = 20) -> List[Notification]:
        return self.db.query(Notification)\
            .filter(Notification.id_receiver == user_id, Notification.is_read == False)\
            .order_by(Notification.created_at.desc())\
            .offset(skip).limit(limit).all()

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification