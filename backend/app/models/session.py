import asyncio
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.constants import (
    BiologicalSex,
    ClinicalStatus,
    MessageRole,
    PregnancyStatus,
    TriageLevel,
)


class ChatMessage(BaseModel):
    role: MessageRole
    content: str = Field(..., max_length=4000)
    triage_level: TriageLevel | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EphemeralPatientProfile(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    age_years: int = Field(..., ge=0, le=125)
    age_months: int | None = Field(default=None, ge=0, le=23)
    biological_sex: BiologicalSex
    pregnancy_status: PregnancyStatus = PregnancyStatus.UNKNOWN
    medications_status: ClinicalStatus = ClinicalStatus.UNKNOWN
    medications: list[str] = Field(default_factory=list)
    allergies_status: ClinicalStatus = ClinicalStatus.UNKNOWN
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions_status: ClinicalStatus = ClinicalStatus.UNKNOWN
    chronic_conditions: list[str] = Field(default_factory=list)
    country_code: str = Field(default="US", min_length=2, max_length=2)


class EphemeralDocument(BaseModel):
    document_id: str
    filename: str = Field(..., max_length=100)
    page_count: int = Field(..., ge=1, le=10)
    total_characters: int = Field(default=0)
    text_by_page: dict[int, str] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EphemeralSession(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        + timedelta(minutes=settings.SESSION_TTL_MINUTES)
    )
    terminated: bool = False
    highest_triage_level: TriageLevel = TriageLevel.GREEN
    profile: EphemeralPatientProfile
    chat_history: list[ChatMessage] = Field(default_factory=list)
    documents: list[EphemeralDocument] = Field(default_factory=list)
    lock: asyncio.Lock = Field(default_factory=asyncio.Lock, exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def refresh_ttl(self) -> None:
        now = datetime.now(timezone.utc)
        self.last_activity = now
        self.expires_at = now + timedelta(minutes=settings.SESSION_TTL_MINUTES)
