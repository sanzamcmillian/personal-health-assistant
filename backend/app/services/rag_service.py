from pathlib import Path

from app.models.chunk import DocumentChunk
from app.services.gemini_service import GeminiService
from app.services.retrieval_service import RetrievalService

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "system_prompt.txt"
)

NO_CONTEXT_ANSWER = (
    "I don't have any documents to answer that from yet. "
    "Upload a PDF first, then ask again."
)


class RagService:
    """
    Answers a question using only the content of previously uploaded
    documents: retrieves relevant chunks, builds a grounded prompt, and
    asks Gemini to generate an answer from that context only.
    """

    def __init__(
        self,
        retrieval: RetrievalService,
        gemini: GeminiService,
    ):
        self.retrieval = retrieval
        self.gemini = gemini

    def answer(
        self,
        question: str,
        top_k: int = 5,
    ) -> dict:
        chunks = self.retrieval.retrieve(question, top_k=top_k)

        if not chunks:
            return {
                "answer": NO_CONTEXT_ANSWER,
                "sources": [],
            }

        prompt = self._build_prompt(question, chunks)
        answer = self.gemini.generate(prompt)

        return {
            "answer": answer,
            "sources": self._build_sources(chunks),
        }

    def _build_prompt(
        self,
        question: str,
        chunks: list[DocumentChunk],
    ) -> str:
        template = PROMPT_PATH.read_text()
        context = self._build_context(chunks)

        return template.format(
            context=context,
            question=question,
        )

    @staticmethod
    def _build_context(chunks: list[DocumentChunk]) -> str:
        parts = [
            f"[Source: {chunk.document.original_filename}, "
            f"page {chunk.page_number}]\n{chunk.content}"
            for chunk in chunks
        ]
        return "\n\n".join(parts)

    @staticmethod
    def _build_sources(chunks: list[DocumentChunk]) -> list[dict]:
        return [
            {
                "document_id": str(chunk.document_id),
                "filename": chunk.document.original_filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ]