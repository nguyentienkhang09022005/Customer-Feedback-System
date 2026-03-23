from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.schemas.baseHumanSchema import BaseHumanCreate, HumanOut
from app.core.constants import HumanStatusEnum

class EmployeeCreate(BaseHumanCreate):
    department: str
    job_title: str
    role_name: str
    hire_date: date
    avatar: Optional[str] = None

class EmployeeOut(HumanOut):
    employee_code: str
    department: str
    job_title: str
    max_ticket_capacity: int
    csat_score: float
    role_name: str
    avatar: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = Field(None, pattern=r"^[0-9]{10,15}$")
    department: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[HumanStatusEnum] = None
    avatar: Optional[str] = None