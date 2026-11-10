import asyncio
import io
import re
import secrets
import fitz  # PyMuPDF
from fastapi import HTTPException, UploadFile, status
from app.core.config import settings
from app.models.session import EphemeralDocument

# Global concurrency limiter for CPU-bound PyMuPDF extractions
_EXTRACTION_SEMAPHORE = asyncio.Semaphore(3)
_EXTRACTION_TIMEOUT_SECONDS = 5.0
_CHUNK_READ_SIZE = 64 * 1024  # 64 KB


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "uploaded_document.pdf"
    # Strip paths, XML/HTML tags, and non-alphanumeric chars (keep ._-)
    clean = re.sub(r"[^\w\.\-]", "_", filename.strip())
    return clean[:100]


class PDFService:
    """
    Parses PDF files in-memory using streaming size limits and threadpool extraction.
    Zero disk storage. Validates magic bytes, page limits, encryption, and scanned status.
    """

    @classmethod
    async def process_upload(cls, file: UploadFile) -> EphemeralDocument:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DOCUMENT_FORMAT", "detail": "Only PDF files are supported."},
            )

        # 1. Stream file bytes with strict size enforcement (chunk by chunk)
        buffer = io.BytesIO()
        bytes_read = 0

        while True:
            chunk = await file.read(_CHUNK_READ_SIZE)
            if not chunk:
                break
            bytes_read += len(chunk)
            if bytes_read > settings.MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "code": "FILE_TOO_LARGE",
                        "detail": f"File exceeds maximum upload limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.",
                    },
                )
            buffer.write(chunk)

        file_bytes = buffer.getvalue()

        # 2. Magic Bytes Validation
        if not file_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DOCUMENT_FORMAT", "detail": "Invalid file format. Must be a valid PDF document."},
            )

        # 3. Threadpool extraction with concurrency semaphore & timeout
        async with _EXTRACTION_SEMAPHORE:
            try:
                doc_data = await asyncio.wait_for(
                    asyncio.to_thread(cls._extract_pdf_in_thread, file_bytes),
                    timeout=_EXTRACTION_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail={"code": "UPSTREAM_TIMEOUT", "detail": "Document text extraction timed out."},
                )

        page_count, total_chars, text_by_page = doc_data

        # 4. Scanned PDF Detection (Check per-page character density)
        if total_chars < (page_count * 50):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "SCANNED_DOCUMENT",
                    "detail": "This document appears to be a scanned image or photo without selectable text. Please describe your key findings in chat or provide a text-based PDF.",
                },
            )

        doc_id = f"doc_{secrets.token_hex(6)}"
        safe_name = sanitize_filename(file.filename)

        return EphemeralDocument(
            document_id=doc_id,
            filename=safe_name,
            page_count=page_count,
            total_characters=total_chars,
            text_by_page=text_by_page,
        )

    @staticmethod
    def _extract_pdf_in_thread(file_bytes: bytes) -> tuple[int, int, dict[int, str]]:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DOCUMENT_FORMAT", "detail": "Could not open PDF. The file may be corrupt."},
            )

        # Check encryption
        if doc.is_encrypted:
            doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DOCUMENT_FORMAT", "detail": "Password-protected or encrypted PDFs are not supported."},
            )

        # Check page count before iterating through text
        page_count = len(doc)
        if page_count > settings.MAX_PAGES_PER_DOCUMENT:
            doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "PAGE_LIMIT_EXCEEDED",
                    "detail": f"PDF has {page_count} pages, which exceeds the limit of {settings.MAX_PAGES_PER_DOCUMENT} pages.",
                },
            )

        text_by_page: dict[int, str] = {}
        total_chars = 0

        for page_idx in range(page_count):
            page_text = doc[page_idx].get_text() or ""
            cleaned = page_text.strip()
            total_chars += len(cleaned)
            text_by_page[page_idx + 1] = cleaned

        doc.close()
        return page_count, total_chars, text_by_page


pdf_service = PDFService()