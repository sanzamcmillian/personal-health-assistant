import json
from google import genai
from google.genai import types
from app.core.config import settings
from app.prompts.triage_prompt import GEMINI_RESPONSE_SCHEMA, TRIAGE_SYSTEM_PROMPT


class GeminiService:
    """
    Interfaces with Google Gemini 2.5 Flash to generate
    structured JSON triage evaluations adhering to OpenAPI specs.
    Handles rate limits (429), timeouts, and safety blocks gracefully.
    """

    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def evaluate_triage(self, prompt_content: str) -> dict:
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_content,
                config=types.GenerateContentConfig(
                    system_instruction=TRIAGE_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=GEMINI_RESPONSE_SCHEMA,
                    temperature=0.2,
                ),
            )

            text = response.text or "{}"
            return json.loads(text)
        except Exception:
            # Safe structured fallback on 429, timeout, network error, or safety block
            return {
                "triage_level": "YELLOW",
                "disposition": "PRIMARY_CARE_48H",
                "assessment_status": "NEEDS_MORE_INFO",
                "reasoning_summary": (
                    "I was unable to complete an automated evaluation of your symptoms at this time. "
                    "If you are concerned about your condition or in significant discomfort, please contact "
                    "local emergency services or seek prompt in-person medical care."
                ),
                "possible_causes": [],
                "warning_signs": [
                    "Sudden severe pain",
                    "Difficulty breathing or shortness of breath",
                    "Chest tightness or dizziness",
                ],
                "follow_up_questions": [],
                "extracted_profile_updates": {
                    "medications_mentioned": [],
                    "allergies_mentioned": [],
                    "chronic_conditions_mentioned": [],
                },
                "citations": [],
                "uncertainty_note": "Automated evaluation could not be completed safely by upstream services.",
            }


gemini_service = GeminiService()