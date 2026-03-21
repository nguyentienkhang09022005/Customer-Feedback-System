import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Integer, UUID
from datetime import datetime
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id_log = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    log_type = Column(String(50))
    action = Column(String(255), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    id_reference = Column(UUID(as_uuid=True))
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee"))


class FAQArticle(Base):
    __tablename__ = "faq_articles"
    id_article = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_category = Column(UUID(as_uuid=True), ForeignKey("tickets_category.id_category"))
    id_author = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee"))