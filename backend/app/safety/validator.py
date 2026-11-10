import re
from typing import Any
from app.core.constants import TriageDisposition, TriageLevel
from app.models.session import EphemeralDocument

TRIAGE_SEVERITY = {
    TriageLevel.GREEN: 1,
    TriageLevel.YELLOW: 2,
    TriageLevel.RED: 3,
}

# Dangerous phrasing: telling patients to unilaterally stop medications or adjust dosage
STOP_MED_PATTERN = re.compile(
    r"\b(stop\s+taking|discontinue|cease)\s+([a-zA-Z0-9\s\-]+)",
    re.IGNORECASE,
)
DOSING_PATTERN = re.compile(
    r"\b(take|increase|decrease|double)\s+(to\s+)?\d+(\.\d+)?\s*(mg|mcg|ml|g|tablets?|pills?)\b",
    re.IGNORECASE,
)


class PostLLMValidator:
    """
    Validates and sanitizes LLM-generated structured triage outputs:
    1. Enforces a sticky escalation floor: max(rules, LLM, session.highest_triage_level).
    2. Strips/remedies medication stopping directives or explicit dosing changes.
    3. Programmatically verifies cited snippets and page numbers against actual documents.
    """

    @classmethod
    def validate(
        cls,
        parsed_output: dict[str, Any],
        baseline_floor: TriageLevel = TriageLevel.GREEN,
        documents: list[EphemeralDocument] | None = None,
    ) -> dict[str, Any]:
        output = dict(parsed_output)

        # 1. Sticky Escalation Floor enforcement: max(LLM, baseline_floor)
        raw_level = output.get("triage_level", TriageLevel.GREEN)
        try:
            llm_level = TriageLevel(raw_level)
        except ValueError:
            llm_level = TriageLevel.YELLOW

        if TRIAGE_SEVERITY[llm_level] < TRIAGE_SEVERITY[baseline_floor]:
            final_level = baseline_floor
            # If floor was RED, elevate disposition as well
            if final_level == TriageLevel.RED:
                output["disposition"] = TriageDisposition.EMERGENCY_ROOM_IMMEDIATELY.value
        else:
            final_level = llm_level

        output["triage_level"] = final_level.value

        # 2. Medication Guardrail
        summary = output.get("reasoning_summary", "")
        if STOP_MED_PATTERN.search(summary):
            summary = STOP_MED_PATTERN.sub(
                r"discuss your \2 regimen with your prescribing doctor before making any changes",
                summary,
            )
        if DOSING_PATTERN.search(summary):
            summary = DOSING_PATTERN.sub(
                "[dosage should be confirmed with your doctor]",
                summary,
            )
        output["reasoning_summary"] = summary

        # 3. Server-Side Literal Citation Verification
        if documents and "citations" in output and isinstance(output["citations"], list):
            doc_map = {doc.filename: doc for doc in documents}
            verified_citations = []

            for citation in output["citations"]:
                if isinstance(citation, dict):
                    fname = citation.get("filename")
                    page = citation.get("page_number")
                    snippet = citation.get("snippet", "").strip()

                    # Find doc by exact or sanitized filename
                    target_doc = doc_map.get(fname)
                    if not target_doc and fname:
                        # Fallback match if user uploaded single file
                        if len(documents) == 1:
                            target_doc = documents[0]

                    if target_doc and page in target_doc.text_by_page:
                        page_text = target_doc.text_by_page[page]
                        # Check if snippet literally exists as a substring (case-insensitive)
                        if snippet and snippet.lower() in page_text.lower():
                            citation["filename"] = target_doc.filename
                            verified_citations.append(citation)

            output["citations"] = verified_citations
        else:
            output["citations"] = []

        return output
