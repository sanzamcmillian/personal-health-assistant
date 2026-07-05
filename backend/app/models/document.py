from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Document(BaseModel):

    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(255))

    original_filename: Mapped[str] = mapped_column(String(255))

    mime_type: Mapped[str] = mapped_column(String(100))

    storage_path: Mapped[str] = mapped_column(String(500))

    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )