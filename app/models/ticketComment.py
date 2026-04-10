import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, UUID, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class TicketComment(Base):
    __tablename__ = "ticket_comments"
    
    id_comment = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    id_ticket = Column(UUID(as_uuid=True), ForeignKey("tickets.id_ticket", ondelete="CASCADE"), nullable=False)
    id_author = Column(UUID(as_uuid=True), ForeignKey("humans.id", ondelete="CASCADE"), nullable=False)
    author_type = Column(String(20), nullable=False)  # "customer" hoặc "employee"
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Chỉ employee mới thấy internal notes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("Human")
