from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


class SourceItem(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]