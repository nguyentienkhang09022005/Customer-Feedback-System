from fastapi import APIRouter
from app.schemas.constants import (
    TicketStatusesResponse,
    MembershipTiersResponse,
    SeverityLevelsResponse,
    HumanStatusesResponse,
    SentimentLabelsResponse,
    SystemLimitsResponse
)
from app.core.constants import (
    TicketStatusConstants,
    MembershipTierEnum,
    HumanStatusEnum,
    SeverityEnum,
    SentimentLabel,
    SentimentConstants,
    SystemConstants
)

router = APIRouter(prefix="/constants", tags=["Constants"])


@router.get("/ticket-statuses", response_model=TicketStatusesResponse)
def get_ticket_statuses():
    """Lấy danh sách trạng thái ticket và các transitions.
    - all_statuses: Tất cả trạng thái
    - active_statuses: Trạng thái đang xử lý
    - closed_statuses: Trạng thái đã đóng (Resolved, Closed, Cancelled)
    - status_transitions: Mapping chuyển trạng thái hợp lệ
    """
    return TicketStatusesResponse(
        all_statuses=TicketStatusConstants.VALID_STATUSES,
        active_statuses=TicketStatusConstants.ACTIVE_STATUSES,
        closed_statuses=["Resolved", "Closed", "Cancelled"],
        status_transitions=TicketStatusConstants.STATUS_TRANSITIONS
    )


@router.get("/membership-tiers", response_model=MembershipTiersResponse)
def get_membership_tiers():
    """Lấy danh sách hạng khách hàng.
    Các hạng: Standard, Silver, Gold, Platinum
    """
    return MembershipTiersResponse(
        tiers=[t.value for t in MembershipTierEnum]
    )


@router.get("/severity-levels", response_model=SeverityLevelsResponse)
def get_severity_levels():
    """Lấy mức độ nghiêm trọng của ticket.
    Các mức: Low (Thấp), Medium (Trung bình), High (Cao), Critical (Nghiêm trọng)
    """
    return SeverityLevelsResponse(
        levels=[s.value for s in SeverityEnum]
    )


@router.get("/human-statuses", response_model=HumanStatusesResponse)
def get_human_statuses():
    """Lấy trạng thái tài khoản người dùng.
    - Active: Tài khoản đang hoạt động
    - Inactive: Tài khoản bị vô hiệu hóa
    - Banned: Tài khoản bị khóa
    - Pending: Chờ xác minh email
    """
    return HumanStatusesResponse(
        statuses=[s.value for s in HumanStatusEnum]
    )


@router.get("/sentiment-labels", response_model=SentimentLabelsResponse)
def get_sentiment_labels():
    """Lấy nhãn phân tích cảm xúc.
    - positive: Tích cực (score >= 0.3)
    - neutral: Trung tính (-0.3 < score < 0.3)
    - negative: Tiêu cực (score <= -0.3)
    """
    return SentimentLabelsResponse(
        labels=[s.value for s in SentimentLabel]
    )


@router.get("/system-limits", response_model=SystemLimitsResponse)
def get_system_limits():
    """Lấy các giới hạn và ngưỡng của hệ thống.
    - rate_limit_tickets: Số ticket được tạo tối đa trong 1 khoảng thời gian
    - rate_limit_window_seconds: Khoảng thời gian áp dụng rate limit (giây)
    - default_max_ticket_capacity: Số ticket tối đa mặc định 1 user có thể tạo
    - positive_threshold: Ngưỡng để coi là sentiment tích cực
    - negative_threshold: Ngưỡng để coi là sentiment tiêu cực
    """
    return SystemLimitsResponse(
        rate_limit_tickets=TicketStatusConstants.RATE_LIMIT_TICKETS,
        rate_limit_window_seconds=TicketStatusConstants.RATE_LIMIT_WINDOW_SECONDS,
        default_max_ticket_capacity=SystemConstants.DEFAULT_MAX_TICKET_CAPACITY,
        positive_threshold=SentimentConstants.POSITIVE_THRESHOLD,
        negative_threshold=SentimentConstants.NEGATIVE_THRESHOLD
    )
