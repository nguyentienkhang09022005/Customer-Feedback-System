import uuid
from sqlalchemy import Column, String, DateTime, Text, Boolean, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"
    id_department = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
