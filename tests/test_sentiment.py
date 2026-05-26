"""
Tests for SentimentService - sentiment reporting and analysis.
"""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.services.sentimentService import SentimentService
from app.models.sentiment import SentimentReport
from app.core.constants import SentimentScope


@pytest.fixture
def sentiment_service(db_session):
    """Create sentiment service instance."""
    return SentimentService(db_session)


@pytest.fixture
def sample_sentiment_report(db_session):
    """Create a sample sentiment report."""
    report = SentimentReport(
        id_report=uuid4(),
        year=2026,
        month=5,
        scope=SentimentScope.SYSTEM.value,
        positive_count=150,
        neutral_count=80,
        negative_count=30,
        avg_sentiment_score=0.65,
        total_interactions=260,
        avg_response_time_hours=4.5,
        resolution_rate=0.85,
        message_positive=100,
        message_neutral=50,
        message_negative=20,
        evaluation_positive=30,
        evaluation_neutral=20,
        evaluation_negative=5,
        comment_positive=20,
        comment_neutral=10,
        comment_negative=5
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture
def sample_department_sentiment_report(db_session, sample_department):
    """Create a department-level sentiment report."""
    report = SentimentReport(
        id_report=uuid4(),
        year=2026,
        month=5,
        scope=SentimentScope.DEPARTMENT.value,
        id_department=sample_department.id_department,
        positive_count=50,
        neutral_count=30,
        negative_count=10,
        avg_sentiment_score=0.58,
        total_interactions=90,
        avg_response_time_hours=3.2,
        resolution_rate=0.88,
        message_positive=35,
        message_neutral=20,
        message_negative=5,
        evaluation_positive=10,
        evaluation_neutral=8,
        evaluation_negative=3,
        comment_positive=5,
        comment_neutral=2,
        comment_negative=2
    )
    db_session.add(report)
    db_session.commit()
    return report


class TestSentimentServiceSystem:
    """Tests for system-level sentiment retrieval."""

    def test_get_system_sentiment_returns_report(
        self, sentiment_service, sample_sentiment_report
    ):
        """get_system_sentiment should return sentiment report for system scope."""
        result = sentiment_service.get_system_sentiment(2026, 5)

        assert result is not None
        assert result.year == 2026
        assert result.month == 5
        assert result.scope == SentimentScope.SYSTEM.value
        assert result.sentiment_breakdown["positive"] == 150

    def test_get_system_sentiment_raises_404_when_no_data(
        self, sentiment_service
    ):
        """get_system_sentiment should raise 404 when no data exists."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            sentiment_service.get_system_sentiment(2020, 1)

        assert exc_info.value.status_code == 404
        assert "No sentiment data" in str(exc_info.value.detail)


class TestSentimentServiceDepartment:
    """Tests for department-level sentiment retrieval."""

    def test_get_department_sentiment_returns_report(
        self, sentiment_service, sample_department_sentiment_report, sample_department
    ):
        """get_department_sentiment should return report for specific department."""
        result = sentiment_service.get_department_sentiment(
            2026, 5, sample_department.id_department
        )

        assert result is not None
        assert result.id_department == sample_department.id_department
        assert result.sentiment_breakdown["positive"] == 50

    def test_get_department_sentiment_blocks_other_department(
        self, sentiment_service, sample_department_sentiment_report, sample_department, sample_department_2
    ):
        """get_department_sentiment should block access to other department's data."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            sentiment_service.get_department_sentiment(
                2026, 5, sample_department_2.id_department,
                requesting_user_dept_id=sample_department.id_department
            )

        assert exc_info.value.status_code == 403
        assert "your own department" in str(exc_info.value.detail)

    def test_get_my_department_sentiment_allows_own_department(
        self, sentiment_service, sample_department_sentiment_report, sample_department
    ):
        """get_my_department_sentiment should allow access with matching dept."""
        result = sentiment_service.get_my_department_sentiment(
            2026, 5, sample_department.id_department
        )

        assert result is not None
        assert result.id_department == sample_department.id_department


class TestSentimentServiceTrends:
    """Tests for sentiment trend analysis."""

    def test_get_system_trends_returns_trends_response(
        self, sentiment_service, sample_sentiment_report
    ):
        """get_system_trends should return trend data for the year."""
        result = sentiment_service.get_system_trends(2026)

        assert result is not None
        assert hasattr(result, "labels")
        assert hasattr(result, "positive_data")
        assert hasattr(result, "neutral_data")
        assert hasattr(result, "negative_data")
        assert hasattr(result, "avg_score_data")

    def test_get_department_trends_returns_trends_response(
        self, sentiment_service, sample_department_sentiment_report, sample_department
    ):
        """get_department_trends should return department-specific trends."""
        result = sentiment_service.get_department_trends(2026, sample_department.id_department)

        assert result is not None
        assert hasattr(result, "labels")

    def test_get_department_trends_blocks_other_department(
        self, sentiment_service, sample_department, sample_department_2
    ):
        """get_department_trends should block access to other department trends."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            sentiment_service.get_department_trends(
                2026, sample_department_2.id_department,
                requesting_user_dept_id=sample_department.id_department
            )

        assert exc_info.value.status_code == 403


class TestSentimentServiceCompare:
    """Tests for sentiment comparison between periods."""

    def test_compare_sentiment_returns_compare_response(
        self, sentiment_service, db_session
    ):
        """compare_sentiment should return comparison between two periods."""
        from datetime import datetime

        # Create two reports
        report1 = SentimentReport(
            id_report=uuid4(),
            year=2026,
            month=4,
            scope=SentimentScope.SYSTEM.value,
            positive_count=100,
            neutral_count=60,
            negative_count=40,
            avg_sentiment_score=0.5,
            total_interactions=200,
            avg_response_time_hours=5.0,
            resolution_rate=0.80
        )
        report2 = SentimentReport(
            id_report=uuid4(),
            year=2026,
            month=5,
            scope=SentimentScope.SYSTEM.value,
            positive_count=150,
            neutral_count=80,
            negative_count=30,
            avg_sentiment_score=0.65,
            total_interactions=260,
            avg_response_time_hours=4.5,
            resolution_rate=0.85
        )
        db_session.add(report1)
        db_session.add(report2)
        db_session.commit()

        result = sentiment_service.compare_sentiment(2026, 4, 2026, 5, "system")

        assert result is not None
        assert hasattr(result, "from_period")
        assert hasattr(result, "to_period")
        assert hasattr(result, "change_percentage")
        assert hasattr(result, "change_absolute")
        assert result.from_period["positive"] == 100
        assert result.to_period["positive"] == 150

    def test_compare_sentiment_raises_404_when_data_missing(
        self, sentiment_service
    ):
        """compare_sentiment should raise 404 when comparison data is incomplete."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            sentiment_service.compare_sentiment(2020, 1, 2020, 6, "system")

        assert exc_info.value.status_code == 404
        assert "Missing data" in str(exc_info.value.detail)


class TestSentimentServiceByDepartment:
    """Tests for sentiment aggregated by department."""

    def test_get_sentiment_by_department_returns_departments(
        self, sentiment_service, sample_department_sentiment_report
    ):
        """get_sentiment_by_department should return list of department summaries."""
        result = sentiment_service.get_sentiment_by_department(2026, 5)

        assert result is not None
        assert hasattr(result, "departments")
        assert isinstance(result.departments, list)
        assert len(result.departments) >= 1

    def test_get_sentiment_by_department_includes_department_names(
        self, sentiment_service, sample_department_sentiment_report, sample_department
    ):
        """Each department summary should include department name."""
        result = sentiment_service.get_sentiment_by_department(2026, 5)

        dept = result.departments[0]
        assert hasattr(dept, "department_name")
        assert dept.department_name == sample_department.name


class TestSentimentServiceResponseBuilding:
    """Tests for internal response building methods."""

    def test_build_summary_response_includes_sentiment_breakdown(
        self, sentiment_service, sample_sentiment_report
    ):
        """_build_summary_response should include sentiment breakdown."""
        result = sentiment_service.get_system_sentiment(2026, 5)

        assert hasattr(result, "sentiment_breakdown")
        assert "positive" in result.sentiment_breakdown
        assert "neutral" in result.sentiment_breakdown
        assert "negative" in result.sentiment_breakdown

    def test_build_summary_response_includes_by_source_breakdown(
        self, sentiment_service, sample_sentiment_report
    ):
        """_build_summary_response should include breakdown by source."""
        result = sentiment_service.get_system_sentiment(2026, 5)

        assert hasattr(result, "by_source")
        assert "messages" in result.by_source
        assert "evaluations" in result.by_source
        assert "comments" in result.by_source

    def test_build_summary_response_includes_metrics(
        self, sentiment_service, sample_sentiment_report
    ):
        """_build_summary_response should include performance metrics."""
        result = sentiment_service.get_system_sentiment(2026, 5)

        assert hasattr(result, "metrics")
        assert "avg_response_time_hours" in result.metrics
        assert "resolution_rate" in result.metrics

    def test_build_trends_response_includes_labels_and_data(
        self, sentiment_service, sample_sentiment_report
    ):
        """_build_trends_response should include all required data arrays."""
        result = sentiment_service.get_system_trends(2026)

        assert len(result.labels) == len(result.positive_data)
        assert len(result.labels) == len(result.neutral_data)
        assert len(result.labels) == len(result.negative_data)
        assert len(result.labels) == len(result.avg_score_data)