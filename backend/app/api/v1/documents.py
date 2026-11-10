from fastapi import APIRouter, Cookie, File, HTTPException, Request, UploadFile, status
from app.core.config import settings
from app.core.rate_limit import rate_limiter
from app.schemas.document import DocumentDeleteResponse, DocumentUploadResponse
from app.services.pdf_service import pdf_service
from app.services.session_service import session_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> DocumentUploadResponse:
    rate_limiter.check(request)

    session = await session_service.get_session(session_token)

    async with session.lock:
        if len(session.documents) >= settings.MAX_DOCUMENTS_PER_SESSION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "MAX_DOCUMENTS_REACHED",
                    "detail": f"Maximum limit of {settings.MAX_DOCUMENTS_PER_SESSION} documents per session reached.",
                },
            )

        doc = await pdf_service.process_upload(file)
        session.documents.append(doc)

    return DocumentUploadResponse(
        document_id=doc.document_id,
        filename=doc.filename,
        page_count=doc.page_count,
        total_characters=doc.total_characters,
        message=f"Document '{doc.filename}' uploaded and indexed in memory for this session.",
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    request: Request,
    session_token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
) -> DocumentDeleteResponse:
    rate_limiter.check(request)

    session = await session_service.get_session(session_token)

    async with session.lock:
        initial_len = len(session.documents)
        session.documents = [d for d in session.documents if d.document_id != document_id]
        if len(session.documents) == initial_len:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "DOCUMENT_NOT_FOUND", "detail": f"Document '{document_id}' not found in active session."},
            )

    return DocumentDeleteResponse(
        document_id=document_id,
        deleted=True,
    )
