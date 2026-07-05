from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.repositories.base_repository import BaseRepository


class ChunkRepository(
    BaseRepository[DocumentChunk]
):

    def __init__(self, db: Session):
        super().__init__(db)

    def get_chunks(
        self,
        document_id,
    ):
        return (
            self.db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id
            )
            .order_by(DocumentChunk.chunk_index)
            .all()
        )