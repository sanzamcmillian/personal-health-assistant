from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.models.base_model import BaseModel


class DocumentChunk(BaseModel):

    __tablename__ = "document_chunks"

    document_id = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
    )

    page_number: Mapped[int] = mapped_column(Integer)

    chunk_index: Mapped[int] = mapped_column(Integer)

    content: Mapped[str] = mapped_column(Text)

    embedding = mapped_column(Vector(768))

    document = relationship(
        "Document",
        back_populates="chunks",
    )