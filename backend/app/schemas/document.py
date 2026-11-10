from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    total_characters: int
    message: str


class DocumentDeleteResponse(BaseModel):
    document_id: str
    deleted: bool