import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketCategory(Base):
    __tablename__ = "tickets_category"
    id_category = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    department = Column(String(50), nullable=False)
    auto_assign = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SLAPolicy(Base):
    __tablename__ = "sla_policies"
    id_policy = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    policy_name = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    max_resolution_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


class Ticket(Base):
    __tablename__ = "tickets"
    id_ticket = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="New")
    severity = Column(String(50))

    version = Column(Integer, nullable=False, default=1)

    expired_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Khóa ngoại cũng phải đổi thành UUID
    id_category = Column(UUID(as_uuid=True), ForeignKey("tickets_category.id_category"))
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee"), nullable=True)
    id_customer = Column(UUID(as_uuid=True), ForeignKey("customers.id_customer"))

    __mapper_args__ = {
        "version_id_col": version
    }