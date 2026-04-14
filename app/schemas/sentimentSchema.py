from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class SentimentReportSchema(BaseModel):
    id_report: UUID
    year: int
    month: int
    scope: str
    id_department: Optional[UUID] = None
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    avg_sentiment_score: Optional[float] = None
    total_interactions: int = 0
    avg_response_time_hours: Optional[float] = None
    resolution_rate: Optional[float] = None
    sentiment_change: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SentimentDetailSchema(BaseModel):
    id_detail: UUID
    id_report: UUID
    source_type: str
    source_id: UUID
    sentiment_label: str
    sentiment_score: float
    id_customer: UUID
    id_ticket: Optional[UUID] = None
    id_department: UUID
    original_content: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SentimentSourceBreakdown(BaseModel):
    positive: int = 0
    neutral: int = 0
    negative: int = 0


class SentimentSummaryResponse(BaseModel):
    year: int
    month: int
    scope: str
    id_department: Optional[UUID] = None
    department_name: Optional[str] = None
    sentiment_breakdown: dict
    avg_sentiment_score: Optional[float] = None
    total_interactions: int = 0
    by_source: dict
    metrics: dict


class SentimentTrendsResponse(BaseModel):
    labels: List[str]
    positive_data: List[int]
    neutral_data: List[int]
    negative_data: List[int]
    avg_score_data: List[float]


class SentimentCompareResponse(BaseModel):
    from_period: dict
    to_period: dict
    change_percentage: float
    change_absolute: int


class SentimentDepartmentSummary(BaseModel):
    id_department: UUID
    department_name: str
    positive_count: int
    neutral_count: int
    negative_count: int
    avg_sentiment_score: Optional[float] = None
    total_interactions: int = 0


class SentimentByDepartmentResponse(BaseModel):
    year: int
    month: int
    departments: List[SentimentDepartmentSummary]