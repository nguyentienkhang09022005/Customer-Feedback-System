import uuid
from sqlalchemy import Column, String, Text, Table, ForeignKey, UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

ticket_tags = Table(
    'ticket_tags',
    Base.metadata,
    Column('ticket_id', UUID(as_uuid=True), ForeignKey('tickets.id_ticket', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id_tag', ondelete='CASCADE'), primary_key=True)
)


class Tag(Base):
    __tablename__ = "tags"

    id_tag = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), nullable=False, default="#000000")
    description = Column(Text, nullable=True)

    tickets = relationship("Ticket", secondary=ticket_tags, back_populates="tags")
