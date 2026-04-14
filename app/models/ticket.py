import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, UUID, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketCategory(Base):
    __tablename__ = "tickets_category"
    
    id_category = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    id_department = Column(UUID(as_uuid=True), ForeignKey("departments.id_department", ondelete="CASCADE"), nullable=False)
    auto_assign = Column(Boolean, default=True)
    
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    templates = relationship("TicketTemplate", back_populates="category")


class SLAPolicy(Base):
    __tablename__ = "sla_policies"
    id_policy = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    policy_name = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    max_resolution_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class TicketTemplate(Base):
    __tablename__ = "ticket_templates"
    
    id_template = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    version = Column(Integer, primary_key=True, default=1)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    fields_config = Column(JSON, nullable=False)
    id_author = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    id_category = Column(UUID(as_uuid=True), ForeignKey("tickets_category.id_category", ondelete="SET NULL"), nullable=True)
    
    category = relationship("TicketCategory", back_populates="templates")
    tickets = relationship("Ticket", back_populates="template")


class Ticket(Base):
    __tablename__ = "tickets"
    
    id_ticket = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    custom_fields = Column(JSON, nullable=True)
    status = Column(String(50), default="New")
    severity = Column(String(50))
    resolution_note = Column(Text)

    version = Column(Integer, nullable=False, default=1)

    expired_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    id_employee = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee", ondelete="SET NULL"), nullable=True)
    id_customer = Column(UUID(as_uuid=True), ForeignKey("customers.id_customer", ondelete="CASCADE"))

    id_template = Column(UUID(as_uuid=True), ForeignKey("ticket_templates.id_template", ondelete="SET NULL"), nullable=True)
    template_version = Column(Integer, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    survey_sent = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    __mapper_args__ = {
        "version_id_col": version
    }

    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan")
    template = relationship("TicketTemplate", foreign_keys=[id_template, template_version], viewonly=True)

    @property
    def is_overdue(self) -> bool:
        if self.expired_date and self.status not in ["Resolved", "Closed"]:
            return datetime.utcnow() > self.expired_date
        return False