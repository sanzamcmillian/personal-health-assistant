import re
from typing import NamedTuple
from app.core.constants import TriageDisposition, TriageLevel


class RedFlagResult(NamedTuple):
    is_emergency: bool
    matched_category: str | None
    guidance: str | None
    disposition: TriageDisposition | None


# Deterministic emergency regex patterns
EMERGENCY_PATTERNS = [
    # Cardiac / Acute Coronary
    (
        "cardiac",
        re.compile(
            r"\b(crushing\s+(chest\s+pain|chest\s+pressure)|chest\s+pain\s+radiating\s+to\s+(left\s+arm|jaw|back)|heart\s+attack|chest\s+tightness\s+and\s+(sweating|vomiting|dizzy))\b",
            re.IGNORECASE,
        ),
        "Immediate emergency evaluation required for acute chest pain / cardiac symptoms.",
        TriageDisposition.CALL_AMBULANCE_NOW,
    ),
    # Neurological / Stroke (FAST symptoms)
    (
        "stroke",
        re.compile(
            r"\b(facial\s+droop(ing)?|slurred\s+speech|sudden\s+weakness\s+on\s+one\s+side|sudden\s+numbness\s+in\s+(arm|face|leg)|sudden\s+loss\s+of\s+vision|can('?t|not)\s+speak\s+clearly)\b",
            re.IGNORECASE,
        ),
        "Immediate emergency evaluation required for potential acute stroke symptoms (FAST).",
        TriageDisposition.CALL_AMBULANCE_NOW,
    ),
    # Respiratory Distress
    (
        "respiratory",
        re.compile(
            r"\b(can('?t|not)\s+breathe|severe\s+shortness\s+of\s+breath|gasping\s+for\s+air|turning\s+blue|stridor|choking)\b",
            re.IGNORECASE,
        ),
        "Immediate emergency evaluation required for acute respiratory distress.",
        TriageDisposition.CALL_AMBULANCE_NOW,
    ),
    # Anaphylaxis / Severe Allergic Reaction
    (
        "anaphylaxis",
        re.compile(
            r"\b(throat\s+closing|tongue\s+swelling|lips?\s+swelling\s+and\s+(difficulty\s+breathing|hives)|anaphylaxis)\b",
            re.IGNORECASE,
        ),
        "Immediate emergency evaluation required for potential anaphylaxis.",
        TriageDisposition.CALL_AMBULANCE_NOW,
    ),
    # Severe Hemorrhage / Trauma
    (
        "severe_bleeding",
        re.compile(
            r"\b(uncontrolled\s+bleeding|coughing\s+up\s+large\s+amounts\s+of\s+blood|vomiting\s+blood|severe\s+head\s+trauma\s+and\s+unconscious)\b",
            re.IGNORECASE,
        ),
        "Immediate emergency evaluation required for acute severe bleeding or head trauma.",
        TriageDisposition.CALL_AMBULANCE_NOW,
    ),
    # Acute Severe Abdominal Pain (Vignette calibration: severe pain 7+/10, suspected surgical abdomen)
    (
        "severe_abdominal",
        re.compile(
            r"\b(severe\s+lower\s+abdominal\s+pain|pain\s+(is\s+)?(7|8|9|10)\s*(/|\s*out\s+of\s*)10|peritoneal|rigid\s+abdomen|unbearable\s+stomach\s+pain)\b",
            re.IGNORECASE,
        ),
        "Immediate same-day emergency evaluation required for acute severe abdominal pain to rule out surgical emergencies (e.g. appendicitis, ectopic pregnancy, torsion).",
        TriageDisposition.EMERGENCY_ROOM_IMMEDIATELY,
    ),
]


class PreLLMRedFlagEngine:
    """
    Deterministic rule engine running BEFORE any LLM invocation.
    Guarantees instant emergency detection regardless of LLM latency,
    rate limits, or model safety filter blocks.
    """

    @classmethod
    def evaluate(cls, message: str) -> RedFlagResult:
        if not message or not message.strip():
            return RedFlagResult(
                is_emergency=False,
                matched_category=None,
                guidance=None,
                disposition=None,
            )

        for category, pattern, guidance, disposition in EMERGENCY_PATTERNS:
            if pattern.search(message):
                return RedFlagResult(
                    is_emergency=True,
                    matched_category=category,
                    guidance=guidance,
                    disposition=disposition,
                )

        return RedFlagResult(
            is_emergency=False,
            matched_category=None,
            guidance=None,
            disposition=None,
        )
