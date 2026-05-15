from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class SystemWideWorkloadItem(BaseModel):
    employee_id: UUID
    name: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    open_tickets: int
    max_capacity: int
    utilization_percent: float
    csat_score: float

    class Config:
        from_attributes = True


class DepartmentSummaryItem(BaseModel):
    department_id: UUID
    department_name: str
    member_count: int
    total_capacity: int
    total_load: int
    utilization_percent: float

    class Config:
        from_attributes = True


class SystemWideWorkloadResponse(BaseModel):
    employees: List[SystemWideWorkloadItem]
    total_employees: int
    total_open_tickets: int
    overall_utilization_percent: float


class DepartmentSummaryResponse(BaseModel):
    departments: List[DepartmentSummaryItem]
    total_departments: int