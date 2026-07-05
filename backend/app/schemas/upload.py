from app.schemas.document import DocumentResponse


class UploadResponse(DocumentResponse):
    chunk_count: int