from pydantic import BaseModel
from typing import Optional


class EscalationRuleCreate(BaseModel):
    name: str
    priority: Optional[str] = None
    condition_type: str  # "time_elapsed", "priority", "category"
    condition_value: str  # "4h", "high", "billing"
    action_type: str  # "reassign", "notify", "escalate"
    action_target: str  # department_id, email address, manager_id
    is_active: bool = True


class EscalationRuleUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[str] = None
    condition_type: Optional[str] = None
    condition_value: Optional[str] = None
    action_type: Optional[str] = None
    action_target: Optional[str] = None
    is_active: Optional[bool] = None


class EscalationRuleOut(BaseModel):
    id: str
    name: str
    priority: Optional[str] = None
    condition_type: str
    condition_value: str
    action_type: str
    action_target: str
    is_active: bool

    class Config:
        from_attributes = True
