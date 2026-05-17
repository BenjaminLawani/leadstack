from enum import StrEnum, IntEnum

class UserRole(IntEnum):
    ADMIN = 1

class LoginMethod(StrEnum):
    GOOGLE = "GOOGLE"
    LOCAL = "LOCAL"

class LeadStatus(StrEnum):
    HOT = "HOT"
    WARM = "WARM"
    COLD = "COLD"

class PipelineStatus(StrEnum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    WON = "WON"
    LOST = "LOST"  
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

class FollowUpType(StrEnum):
    EMAIL = "EMAIL"
    CALL = "CALL"
    MEETING = "MEETING"
    REMINDER = "REMINDER"

class MessageTone(StrEnum):
    FORMAL = "FORMAL"
    CASUAL = "CASUAL"
    PROFESSIONAL = "PROFESSIONAL"
    FRIENDLY = "FRIENDLY"

class NoteTag(StrEnum):
    FOLLOW_UP = "FOLLOW_UP"
    REMINDER = "REMINDER"
    IMPORTANT = "IMPORTANT"
    URGENT = "URGENT"