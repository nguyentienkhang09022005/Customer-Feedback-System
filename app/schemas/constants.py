from pydantic import BaseModel
from typing import List, Dict


class TicketStatusesResponse(BaseModel):
    """Danh sách tất cả trạng thái ticket."""
    all_statuses: List[str]
    active_statuses: List[str]
    closed_statuses: List[str]
    status_transitions: Dict[str, List[str]]


class MembershipTiersResponse(BaseModel):
    """Hạng khách hàng: Standard, Silver, Gold, Platinum."""
    tiers: List[str]


class SeverityLevelsResponse(BaseModel):
    """Mức độ nghiêm trọng: Low, Medium, High, Critical."""
    levels: List[str]


class HumanStatusesResponse(BaseModel):
    """Trạng thái tài khoản: Active, Inactive, Banned, Pending."""
    statuses: List[str]


class SentimentLabelsResponse(BaseModel):
    """Nhãn sentiment: positive, neutral, negative."""
    labels: List[str]


class SystemLimitsResponse(BaseModel):
    """Các giới hạn hệ thống."""
    rate_limit_tickets: int
    rate_limit_window_seconds: int
    default_max_ticket_capacity: int
    positive_threshold: float
    negative_threshold: float
