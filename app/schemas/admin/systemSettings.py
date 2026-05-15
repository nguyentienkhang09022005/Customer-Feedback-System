from pydantic import BaseModel
from typing import Optional


class SystemSettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    allow_customer_registration: Optional[bool] = None
    default_customer_type: Optional[str] = None


class SystemSettingsOut(BaseModel):
    id: str
    company_name: Optional[str] = None
    company_logo: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    maintenance_mode: bool = False
    allow_customer_registration: bool = True
    default_customer_type: Optional[str] = None

    class Config:
        from_attributes = True
