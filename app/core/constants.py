from enum import Enum
from typing import List


class TicketStatusEnum(str, Enum):
    NEW = "New"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    ON_HOLD = "On Hold"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    CANCELLED = "Cancelled"


class TicketStatusConstants:
    VALID_STATUSES: List[str] = [
        "New",
        "In Progress",
        "Pending",
        "On Hold",
        "Resolved",
        "Closed",
        "Cancelled"
    ]
    
    ACTIVE_STATUSES: List[str] = [
        "New",
        "In Progress",
        "Pending",
        "On Hold"
    ]
    
    STATUS_TRANSITIONS: dict = {
        "New": ["In Progress", "Pending", "On Hold", "Cancelled"],
        "In Progress": ["Pending", "On Hold", "Resolved", "Cancelled"],
        "Pending": ["In Progress", "On Hold", "Resolved", "Cancelled"],
        "On Hold": ["In Progress", "Pending", "Resolved", "Cancelled"],
        "Resolved": ["Closed", "In Progress"],
        "Closed": [],
        "Cancelled": ["New"],
    }
    
    RATE_LIMIT_TICKETS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 3600


class HumanStatusEnum(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BANNED = "Banned"
    PENDING = "Pending"  # Awaiting email verification

class MembershipTierEnum(str, Enum):
    STANDARD = "Standard"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"

class SeverityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class SystemConstants:
    DEFAULT_MAX_TICKET_CAPACITY = 5
    DEFAULT_CSAT_SCORE = 0.0


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentSourceType(str, Enum):
    MESSAGE = "message"
    EVALUATION = "evaluation"
    COMMENT = "comment"
    CHATBOT = "chatbot"


class SentimentScope(str, Enum):
    SYSTEM = "system"
    DEPARTMENT = "department"


class SentimentConstants:
    BATCH_SIZE = 50
    SLEEP_BETWEEN_BATCH_SECONDS = 1.0
    SENTIMENT_JOB_INTERVAL_DAYS = 7
    POSITIVE_THRESHOLD = 0.3
    NEGATIVE_THRESHOLD = -0.3
    COMPARE_PREVIOUS_MONTH = 1
    COMPARE_SAME_MONTH_LAST_YEAR = 12


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class AppointmentConstants:
    VALID_STATUSES: List[str] = [
        "pending",
        "accepted",
        "rejected",
        "cancelled",
        "completed"
    ]

    CANCELABLE_STATUSES: List[str] = [
        "pending",
        "accepted"
    ]