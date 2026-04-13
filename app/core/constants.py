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