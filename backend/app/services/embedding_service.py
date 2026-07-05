from app.services.gemini_service import GeminiService


class EmbeddingService:

    def __init__(
        self,
        gemini: GeminiService,
    ):

        self.gemini = gemini

    def create_embedding(
        self,
        text: str,
    ) -> list[float]:

        return self.gemini.embed(text)