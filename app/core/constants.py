from enum import Enum

class HumanStatusEnum(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    BANNED = "Banned"

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