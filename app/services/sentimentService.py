from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.repositories.sentimentRepository import (
    SentimentReportRepository,
    SentimentDetailRepository,
    SentimentDataRepository
)
from app.models.department import Department
from app.schemas.sentimentSchema import (
    SentimentSummaryResponse,
    SentimentTrendsResponse,
    SentimentCompareResponse,
    SentimentByDepartmentResponse,
    SentimentDepartmentSummary
)
from app.core.constants import SentimentScope, SentimentLabel
from typing import Optional, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = SentimentReportRepository(db)
        self.detail_repo = SentimentDetailRepository(db)
        self.data_repo = SentimentDataRepository(db)

    def get_system_sentiment(self, year: int, month: int) -> SentimentSummaryResponse:
        report = self.report_repo.get_by_period_scope(year, month, SentimentScope.SYSTEM.value)
        if not report:
            raise HTTPException(status_code=404, detail="No sentiment data for this period")

        return self._build_summary_response(report, None)

    def get_department_sentiment(
        self,
        year: int,
        month: int,
        id_department: UUID,
        requesting_user_dept_id: Optional[UUID] = None
    ) -> SentimentSummaryResponse:
        if requesting_user_dept_id and requesting_user_dept_id != id_department:
            raise HTTPException(status_code=403, detail="You can only view your own department's sentiment")

        report = self.report_repo.get_by_period_scope(
            year, month, SentimentScope.DEPARTMENT.value, id_department
        )
        if not report:
            raise HTTPException(status_code=404, detail="No sentiment data for this period")

        department = self.data_repo.get_department_by_id(id_department)
        dept_name = department.name if department else None

        return self._build_summary_response(report, dept_name)

    def get_my_department_sentiment(
        self,
        year: int,
        month: int,
        id_department: UUID
    ) -> SentimentSummaryResponse:
        return self.get_department_sentiment(year, month, id_department, id_department)

    def get_system_trends(self, year: int) -> SentimentTrendsResponse:
        reports = self.report_repo.get_system_trends(year)
        return self._build_trends_response(reports)

    def get_department_trends(
        self,
        year: int,
        id_department: UUID,
        requesting_user_dept_id: Optional[UUID] = None
    ) -> SentimentTrendsResponse:
        if requesting_user_dept_id and requesting_user_dept_id != id_department:
            raise HTTPException(status_code=403, detail="You can only view your own department's trends")

        reports = self.report_repo.get_department_trends(year, id_department)
        return self._build_trends_response(reports)

    def compare_sentiment(
        self,
        from_year: int,
        from_month: int,
        to_year: int,
        to_month: int,
        scope: str,
        id_department: Optional[UUID] = None
    ) -> SentimentCompareResponse:
        from_report, to_report = self.report_repo.get_comparison(
            from_year, from_month, to_year, to_month, scope, id_department
        )

        if not from_report or not to_report:
            raise HTTPException(status_code=404, detail="Missing data for comparison")

        from_total = from_report.positive_count + from_report.neutral_count + from_report.negative_count
        to_total = to_report.positive_count + to_report.neutral_count + to_report.negative_count

        change_absolute = to_total - from_total
        change_percentage = ((to_total - from_total) / from_total * 100) if from_total > 0 else 0

        return SentimentCompareResponse(
            from_period={
                "year": from_year,
                "month": from_month,
                "positive": from_report.positive_count,
                "neutral": from_report.neutral_count,
                "negative": from_report.negative_count,
                "avg_score": from_report.avg_sentiment_score
            },
            to_period={
                "year": to_year,
                "month": to_month,
                "positive": to_report.positive_count,
                "neutral": to_report.neutral_count,
                "negative": to_report.negative_count,
                "avg_score": to_report.avg_sentiment_score
            },
            change_percentage=round(change_percentage, 2),
            change_absolute=change_absolute
        )

    def get_sentiment_by_department(self, year: int, month: int) -> SentimentByDepartmentResponse:
        reports = self.report_repo.get_by_department_month(year, month)

        departments = []
        for report in reports:
            dept = self.data_repo.get_department_by_id(report.id_department)
            departments.append(SentimentDepartmentSummary(
                id_department=report.id_department,
                department_name=dept.name if dept else "Unknown",
                positive_count=report.positive_count,
                neutral_count=report.neutral_count,
                negative_count=report.negative_count,
                avg_sentiment_score=report.avg_sentiment_score,
                total_interactions=report.total_interactions
            ))

        return SentimentByDepartmentResponse(
            year=year,
            month=month,
            departments=departments
        )

    def _build_summary_response(self, report, department_name: Optional[str]) -> SentimentSummaryResponse:
        by_source = {
            "messages": {
                "positive": report.message_positive,
                "neutral": report.message_neutral,
                "negative": report.message_negative
            },
            "evaluations": {
                "positive": report.evaluation_positive,
                "neutral": report.evaluation_neutral,
                "negative": report.evaluation_negative
            },
            "comments": {
                "positive": report.comment_positive,
                "neutral": report.comment_neutral,
                "negative": report.comment_negative
            }
        }

        metrics = {
            "avg_response_time_hours": report.avg_response_time_hours,
            "resolution_rate": report.resolution_rate
        }

        return SentimentSummaryResponse(
            year=report.year,
            month=report.month,
            scope=report.scope,
            id_department=report.id_department,
            department_name=department_name,
            sentiment_breakdown={
                "positive": report.positive_count,
                "neutral": report.neutral_count,
                "negative": report.negative_count
            },
            avg_sentiment_score=report.avg_sentiment_score,
            total_interactions=report.total_interactions,
            by_source=by_source,
            metrics=metrics
        )

    def _build_trends_response(self, reports) -> SentimentTrendsResponse:
        labels = []
        positive_data = []
        neutral_data = []
        negative_data = []
        avg_score_data = []

        for report in reports:
            labels.append(f"Tháng {report.month}")
            positive_data.append(report.positive_count)
            neutral_data.append(report.neutral_count)
            negative_data.append(report.negative_count)
            avg_score_data.append(report.avg_sentiment_score or 0.0)

        return SentimentTrendsResponse(
            labels=labels,
            positive_data=positive_data,
            neutral_data=neutral_data,
            negative_data=negative_data,
            avg_score_data=avg_score_data
        )