from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.base_repository import BaseRepository


class DocumentRepository(BaseRepository[Document]):

    def __init__(self, db: Session):
        super().__init__(db)

    def get(self, document_id: UUID) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

    def list(self) -> list[Document]:
        return (
            self.db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

    def find_by_filename(
        self,
        filename: str,
    ) -> Document | None:
        return (
            self.db.query(Document)
            .filter(Document.filename == filename)
            .first()
        )