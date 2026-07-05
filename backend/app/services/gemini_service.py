from google import genai

from app.core.config import settings


class GeminiService:

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

    def generate(
        self,
        prompt: str,
    ) -> str:

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        return response.text

    def embed(
        self,
        text: str,
    ) -> list[float]:

        response = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )

        return response.embeddings[0].values