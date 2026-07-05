from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.init_db import get_db
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.upload import UploadResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.gemini_service import GeminiService
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService
from app.services.upload_service import UploadService

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_upload_service(
    db: Session = Depends(get_db),
) -> UploadService:
    gemini = GeminiService()

    return UploadService(
        storage=StorageService(),
        pdf=PDFService(),
        chunking=ChunkingService(),
        embedding=EmbeddingService(gemini),
        documents=DocumentRepository(db),
        chunks=ChunkRepository(db),
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    upload: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    document, chunk_count = await upload.process(file)

    return UploadResponse(
        id=str(document.id),
        filename=document.filename,
        original_filename=document.original_filename,
        mime_type=document.mime_type,
        created_at=document.created_at,
        chunk_count=chunk_count,
    )