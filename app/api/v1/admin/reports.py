from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.admin.workloadReportService import WorkloadReportService
from app.schemas.admin.workloadReport import (
    SystemWideWorkloadResponse,
    DepartmentSummaryResponse,
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])


@router.get("/workload", response_model=APIResponse[SystemWideWorkloadResponse], dependencies=[Depends(get_current_admin)])
def get_system_wide_workload(db: Session = Depends(get_db)):
    """
    Get system-wide workload report for all employees.
    Returns employee_id, name, department, job_title, open_tickets,
    max_capacity, utilization %, csat_score.
    """
    service = WorkloadReportService(db)
    result = service.get_system_wide_workload()
    return APIResponse(status=True, code=200, message="Success", data=result)


@router.get("/workload/departments", response_model=APIResponse[DepartmentSummaryResponse], dependencies=[Depends(get_current_admin)])
def get_department_summary(db: Session = Depends(get_db)):
    """
    Get department summary workload report.
    Returns department_id, department_name, member_count, total_capacity,
    total_load, utilization %.
    """
    service = WorkloadReportService(db)
    result = service.get_department_summary()
    return APIResponse(status=True, code=200, message="Success", data=result)