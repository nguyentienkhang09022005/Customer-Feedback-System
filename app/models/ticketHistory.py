import uuid
from sqlalchemy import Column, String, DateTime, Text, UUID, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketHistory(Base):
    __tablename__ = "ticket_history"
    
    id_history = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="CASCADE"), nullable=False)
    id_actor = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="SET NULL"), nullable=True)  # Ai thực hiện
    actor_type = Column(String(20))  # "customer", "employee", "system"
    
    action = Column(String(50), nullable=False)  # "created", "status_changed", "assigned", "unassigned", "category_changed", "severity_changed", "resolved", "closed", "reopened"
    old_value = Column(JSON)  # Giá trị cũ
    new_value = Column(JSON)  # Giá trị mới
    note = Column(Text)  # Ghi chú thêm (resolution note, close reason, reopen reason)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    ticket = relationship("Ticket", back_populates="history")
    actor = relationship("Human")


# Action constants for type safety
class TicketAction:
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    CATEGORY_CHANGED = "category_changed"
    SEVERITY_CHANGED = "severity_changed"
    TITLE_CHANGED = "title_changed"
    DESCRIPTION_CHANGED = "description_changed"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    COMMENT_ADDED = "comment_added"
    INTERNAL_NOTE_ADDED = "internal_note_added"
