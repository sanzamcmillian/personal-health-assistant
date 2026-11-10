from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import AssessmentStatus, TriageDisposition, TriageLevel


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class CitationItem(BaseModel):
    filename: str
    page_number: int
    snippet: str
    relevance: str


class PossibleCauseItem(BaseModel):
    name: str
    explanation: str


class TriageResponse(BaseModel):
    triage_level: TriageLevel
    disposition: TriageDisposition
    assessment_status: AssessmentStatus
    is_emergency: bool = False
    reasoning_summary: str
    possible_causes: list[PossibleCauseItem] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    citations: list[CitationItem] = Field(default_factory=list)
    uncertainty_note: str | None = None
    emergency_numbers: list[str] = Field(default_factory=list)
    expires_at: datetime