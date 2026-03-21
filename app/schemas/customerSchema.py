from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.baseHumanSchema import BaseHumanCreate, HumanOut
from app.core.constants import HumanStatusEnum, MembershipTierEnum

class CustomerCreate(BaseHumanCreate):
    timezone: str = Field(..., description="Ví dụ: Asia/Ho_Chi_Minh")
    customer_type: str

class CustomerOut(HumanOut):
    customer_code: str
    membership_tier: str
    timezone: str
    customer_type: str

class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r"^[0-9]{10,15}$")
    timezone: Optional[str] = None
    membership_tier: Optional[MembershipTierEnum] = None
    status: Optional[HumanStatusEnum] = None