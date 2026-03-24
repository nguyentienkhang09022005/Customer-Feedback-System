import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, UUID, Integer
from datetime import datetime
from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"
    id_message = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    message = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="CASCADE"))
    id_sender = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="SET NULL"))


class Attachment(Base):
    __tablename__ = "attachments"
    id_attachment = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    attach_name = Column(String(255))
    attach_type = Column(String(50))
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # id_reference dùng để lưu ID của bảng khác nên cũng phải là UUID
    id_reference = Column(UUID(as_uuid=True))
    id_uploader = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="SET NULL"))


class Evaluate(Base):
    __tablename__ = "evaluates"
    id_evaluate = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Cột star giữ nguyên Integer vì nó là số sao đánh giá (1-5)
    star = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="CASCADE"))
    id_customer = Column(UUID(as_uuid=True), ForeignKey("customers.id_customer", ondelete="CASCADE"))


class Notification(Base):
    __tablename__ = "notification"
    id_notification = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    notification_type = Column(String(50))
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    id_reference = Column(UUID(as_uuid=True))
    id_receiver = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="SET NULL"))