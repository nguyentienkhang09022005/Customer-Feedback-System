import uuid
from sqlalchemy import Column, String, Boolean
from app.db.base import Base


class EscalationRule(Base):
    __tablename__ = "escalation_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    priority = Column(String(50), nullable=True)
    condition_type = Column(String(50), nullable=False)  # "time_elapsed", "priority", "category"
    condition_value = Column(String(255), nullable=False)  # "4h", "high", "billing"
    action_type = Column(String(50), nullable=False)  # "reassign", "notify", "escalate"
    action_target = Column(String(255), nullable=False)  # department_id, email address, manager_id
    is_active = Column(Boolean, default=True)
