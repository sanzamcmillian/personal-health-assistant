from enum import Enum

API_PREFIX = "/api/v1"
APP_VERSION = "0.2.0"
DISCLAIMER_VERSION = "v1.0"


class TriageLevel(str, Enum):
    GREEN = "GREEN"      # Self-Care / Monitor
    YELLOW = "YELLOW"    # Routine / Urgent Care within 24-48h
    RED = "RED"          # Immediate Emergency


class TriageDisposition(str, Enum):
    CALL_AMBULANCE_NOW = "CALL_AMBULANCE_NOW"
    EMERGENCY_ROOM_IMMEDIATELY = "EMERGENCY_ROOM_IMMEDIATELY"
    URGENT_CARE_TODAY = "URGENT_CARE_TODAY"
    PRIMARY_CARE_48H = "PRIMARY_CARE_48H"
    SELF_CARE_MONITOR = "SELF_CARE_MONITOR"


class AssessmentStatus(str, Enum):
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    FINAL = "FINAL"


class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class PregnancyStatus(str, Enum):
    UNKNOWN = "unknown"
    NO = "no"
    POSSIBLE = "possible"  # "unsure" is mapped to "possible" for safety


class ClinicalStatus(str, Enum):
    UNKNOWN = "unknown"
    NONE = "none"
    LISTED = "listed"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


# Country-Specific Emergency Dispatch Numbers
EMERGENCY_NUMBERS_BY_COUNTRY: dict[str, list[str]] = {
    "US": ["911"],
    "CA": ["911"],
    "GB": ["999", "112"],
    "ZA": ["10177", "112"],
    "AU": ["000"],
    "NZ": ["111"],
    "IN": ["112"],
    "DEFAULT": ["112"],
}


def resolve_emergency_numbers(country_code: str | None) -> list[str]:
    if not country_code:
        return EMERGENCY_NUMBERS_BY_COUNTRY["DEFAULT"]
    return EMERGENCY_NUMBERS_BY_COUNTRY.get(
        country_code.upper().strip(), EMERGENCY_NUMBERS_BY_COUNTRY["DEFAULT"]
    )


EMERGENCY_DISCLAIMER = (
    "This is an AI-powered symptom assessment aid, not a qualified healthcare professional. "
    "If you or someone around you is experiencing a medical emergency, call emergency services immediately."
)