import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id_appointment = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="CASCADE"), nullable=False)
    id_customer = Column(UUID(as_uuid=True), ForeignKey("customers.id_customer", ondelete="CASCADE"), nullable=False)
    id_employee = Column(UUID(as_uuid=True), ForeignKey("employees.id_employee", ondelete="CASCADE"), nullable=False)

    scheduled_at = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)

    status = Column(String(20), default="pending", nullable=False)
    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="appointments")
    customer = relationship("Customer", backref="appointments")
    employee = relationship("Employee", backref="appointments")