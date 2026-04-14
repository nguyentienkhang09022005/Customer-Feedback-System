from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.sentimentService import SentimentService
from app.schemas.sentimentSchema import (
    SentimentSummaryResponse,
    SentimentTrendsResponse,
    SentimentCompareResponse
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_employee
from app.models.human import Employee
from uuid import UUID

router = APIRouter(prefix="/department", tags=["Department Analytics"])


@router.get("/me/sentiment", response_model=APIResponse[SentimentSummaryResponse])
def get_my_department_sentiment(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get sentiment data for the current employee's department.
    Shortcut endpoint - same as /department/{my_dept_id}/sentiment
    """
    try:
        if not current_employee.id_department:
            raise HTTPException(
                status_code=400,
                detail="You are not assigned to any department"
            )

        service = SentimentService(db)
        data = service.get_my_department_sentiment(
            year, month, current_employee.id_department
        )
        return APIResponse(
            status=True,
            code=200,
            message="Your department sentiment retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/me/sentiment/trends", response_model=APIResponse[SentimentTrendsResponse])
def get_my_department_sentiment_trends(
    year: int = Query(..., ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get monthly sentiment trends for the current employee's department.
    Shortcut endpoint - same as /department/{my_dept_id}/sentiment/trends
    """
    try:
        if not current_employee.id_department:
            raise HTTPException(
                status_code=400,
                detail="You are not assigned to any department"
            )

        service = SentimentService(db)
        data = service.get_department_trends(
            year, current_employee.id_department, current_employee.id_department
        )
        return APIResponse(
            status=True,
            code=200,
            message="Your department sentiment trends retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/{dept_id}/sentiment", response_model=APIResponse[SentimentSummaryResponse])
def get_department_sentiment(
    dept_id: UUID,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get sentiment data for a specific department.
    Employees can only view their own department's sentiment.
    Admins can view any department.
    """
    try:
        service = SentimentService(db)

        user_dept_id = current_employee.id_department
        is_admin = current_employee.role_name == "Admin"

        if not is_admin and user_dept_id != dept_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own department's sentiment"
            )

        data = service.get_department_sentiment(year, month, dept_id, user_dept_id if not is_admin else None)
        return APIResponse(
            status=True,
            code=200,
            message="Department sentiment retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/{dept_id}/sentiment/trends", response_model=APIResponse[SentimentTrendsResponse])
def get_department_sentiment_trends(
    dept_id: UUID,
    year: int = Query(..., ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Get monthly sentiment trends for a department.
    Employees can only view their own department's trends.
    Admins can view any department.
    """
    try:
        service = SentimentService(db)

        user_dept_id = current_employee.id_department
        is_admin = current_employee.role_name == "Admin"

        if not is_admin and user_dept_id != dept_id:
            raise HTTPException(
                status_code=403,
                detail="You can only view your own department's trends"
            )

        data = service.get_department_trends(year, dept_id, user_dept_id if not is_admin else None)
        return APIResponse(
            status=True,
            code=200,
            message="Department sentiment trends retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/{dept_id}/sentiment/compare", response_model=APIResponse[SentimentCompareResponse])
def compare_department_sentiment(
    dept_id: UUID,
    from_year: int = Query(..., ge=2020, le=2100),
    from_month: int = Query(..., ge=1, le=12),
    to_year: int = Query(..., ge=2020, le=2100),
    to_month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_employee: Employee = Depends(get_current_employee)
):
    """Compare sentiment between two periods for a department.
    Employees can only compare their own department.
    Admins can compare any department.
    """
    try:
        service = SentimentService(db)

        user_dept_id = current_employee.id_department
        is_admin = current_employee.role_name == "Admin"

        if not is_admin and user_dept_id != dept_id:
            raise HTTPException(
                status_code=403,
                detail="You can only compare your own department's sentiment"
            )

        data = service.compare_sentiment(
            from_year, from_month, to_year, to_month,
            scope="department",
            id_department=dept_id
        )
        return APIResponse(
            status=True,
            code=200,
            message="Department sentiment comparison retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))