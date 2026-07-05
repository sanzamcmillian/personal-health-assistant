from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.init_db import get_db
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_rag_service(
    db: Session = Depends(get_db),
) -> RagService:
    gemini = GeminiService()
    embedding = EmbeddingService(gemini)
    chunks = ChunkRepository(db)
    retrieval = RetrievalService(embedding, chunks)

    return RagService(retrieval, gemini)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag: RagService = Depends(get_rag_service),
) -> ChatResponse:
    result = rag.answer(request.question)

    return ChatResponse(**result)