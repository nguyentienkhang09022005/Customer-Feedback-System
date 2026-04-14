from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.services.sentimentService import SentimentService
from app.schemas.sentimentSchema import (
    SentimentSummaryResponse,
    SentimentTrendsResponse,
    SentimentCompareResponse,
    SentimentByDepartmentResponse
)
from app.core.response import APIResponse
from app.api.dependencies import get_db, get_current_admin
from app.models.human import Employee
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/sentiment", response_model=APIResponse[SentimentSummaryResponse])
def get_system_sentiment(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Get system-wide sentiment summary for a specific month (Admin only)"""
    try:
        service = SentimentService(db)
        data = service.get_system_sentiment(year, month)
        return APIResponse(
            status=True,
            code=200,
            message="Sentiment data retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/sentiment/trends", response_model=APIResponse[SentimentTrendsResponse])
def get_system_sentiment_trends(
    year: int = Query(..., ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Get monthly sentiment trends for the entire year (Admin only)"""
    try:
        service = SentimentService(db)
        data = service.get_system_trends(year)
        return APIResponse(
            status=True,
            code=200,
            message="Sentiment trends retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/sentiment/compare", response_model=APIResponse[SentimentCompareResponse])
def compare_sentiment(
    from_year: int = Query(..., ge=2020, le=2100),
    from_month: int = Query(..., ge=1, le=12),
    to_year: int = Query(..., ge=2020, le=2100),
    to_month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Compare sentiment between two periods (Admin only)"""
    try:
        service = SentimentService(db)
        data = service.compare_sentiment(
            from_year, from_month, to_year, to_month, "system"
        )
        return APIResponse(
            status=True,
            code=200,
            message="Sentiment comparison retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))


@router.get("/sentiment/by-department", response_model=APIResponse[SentimentByDepartmentResponse])
def get_sentiment_by_department(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current_admin: Employee = Depends(get_current_admin)
):
    """Get sentiment breakdown by department (Admin only)"""
    try:
        service = SentimentService(db)
        data = service.get_sentiment_by_department(year, month)
        return APIResponse(
            status=True,
            code=200,
            message="Department sentiment data retrieved successfully",
            data=data
        )
    except HTTPException as e:
        return APIResponse(status=False, code=e.status_code, message=e.detail)
    except Exception as e:
        return APIResponse(status=False, code=500, message=str(e))