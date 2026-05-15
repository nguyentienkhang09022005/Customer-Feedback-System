import uuid
from sqlalchemy import Column, String, Text, Boolean
from app.db.base import Base


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=uuid.uuid4, index=True)
    company_name = Column(String(255), nullable=True)
    company_logo = Column(String(500), nullable=True)
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(50), nullable=True)
    maintenance_mode = Column(Boolean, default=False)
    allow_customer_registration = Column(Boolean, default=True)
    default_customer_type = Column(String(50), nullable=True)
