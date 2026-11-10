import pytest
from app.core.constants import TriageDisposition, TriageLevel
from app.models.session import EphemeralDocument
from app.safety.validator import PostLLMValidator


def test_escalation_floor_prevents_downgrade():
    # If baseline floor is RED, an LLM output of GREEN must be raised to RED
    raw_output = {
        "triage_level": "GREEN",
        "disposition": "SELF_CARE_MONITOR",
        "reasoning_summary": "You will be fine with rest.",
    }
    validated = PostLLMValidator.validate(raw_output, baseline_floor=TriageLevel.RED)
    assert validated["triage_level"] == "RED"
    assert validated["disposition"] == TriageDisposition.EMERGENCY_ROOM_IMMEDIATELY.value


def test_escalation_floor_allows_upgrade():
    # If baseline floor is GREEN, an LLM output of YELLOW should remain YELLOW
    raw_output = {
        "triage_level": "YELLOW",
        "disposition": "URGENT_CARE_TODAY",
        "reasoning_summary": "Consult your doctor soon.",
    }
    validated = PostLLMValidator.validate(raw_output, baseline_floor=TriageLevel.GREEN)
    assert validated["triage_level"] == "YELLOW"


def test_medication_guardrail_strips_stop_taking():
    raw_output = {
        "triage_level": "YELLOW",
        "reasoning_summary": "You should stop taking Lisinopril immediately if it causes coughing.",
    }
    validated = PostLLMValidator.validate(raw_output)
    assert "stop taking" not in validated["reasoning_summary"].lower()
    assert "discuss your lisinopril regimen with your prescribing doctor" in validated["reasoning_summary"].lower()


def test_medication_guardrail_strips_dosing():
    raw_output = {
        "triage_level": "YELLOW",
        "reasoning_summary": "You can take 500mg of paracetamol for the fever.",
    }
    validated = PostLLMValidator.validate(raw_output)
    assert "500mg" not in validated["reasoning_summary"]
    assert "[dosage should be confirmed with your doctor]" in validated["reasoning_summary"]


def test_citation_verification_drops_invalid_snippets():
    doc = EphemeralDocument(
        document_id="doc_123",
        filename="lab_test.pdf",
        page_count=1,
        total_characters=100,
        text_by_page={1: "Patient shows elevated WBC count of 14,000 /uL."},
    )

    raw_output = {
        "triage_level": "YELLOW",
        "citations": [
            {
                "filename": "lab_test.pdf",
                "page_number": 1,
                "snippet": "elevated WBC count",
                "relevance": "Indicates infection",
            },
            {
                "filename": "lab_test.pdf",
                "page_number": 1,
                "snippet": "phantom quote not in text",
                "relevance": "Made up",
            },
            {
                "filename": "lab_test.pdf",
                "page_number": 2,  # Page does not exist
                "snippet": "elevated WBC count",
                "relevance": "Invalid page",
            },
        ],
    }

    validated = PostLLMValidator.validate(raw_output, documents=[doc])
    assert len(validated["citations"]) == 1
    assert validated["citations"][0]["snippet"] == "elevated WBC count"
