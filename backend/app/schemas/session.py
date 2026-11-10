from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import BiologicalSex, DISCLAIMER_VERSION, TriageLevel


class StartSessionRequest(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    age_years: int = Field(..., ge=0, le=125)
    age_months: int | None = Field(default=None, ge=0, le=23)
    biological_sex: BiologicalSex
    country_code: str = Field(default="US", min_length=2, max_length=2)


class SessionResponse(BaseModel):
    # session_id is deliberately excluded from JSON body to defeat XSS leakage.
    # It is conveyed exclusively in the HttpOnly cookie.
    age_years: int
    biological_sex: BiologicalSex
    country_code: str
    emergency_numbers: list[str]
    expires_at: datetime
    disclaimer_version: str = DISCLAIMER_VERSION


class SessionStatusResponse(BaseModel):
    active: bool
    expires_at: datetime
    seconds_remaining: int
    highest_triage_level: TriageLevel
    documents_count: int


class KeepAliveResponse(BaseModel):
    refreshed: bool
    expires_at: datetime


class EndSessionResponse(BaseModel):
    message: str
    purged: bool
