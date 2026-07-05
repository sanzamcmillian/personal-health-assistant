from sqlalchemy.orm import Session, joinedload

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

    def similarity_search(self, embedding: list[float], top_k: int = 5) -> list[DocumentChunk]:
        """
        Returns the top_k chunks whose embeddings are closest (cosine
        distance) to the given query embedding. Eager-loads the parent
        Document so callers can build source citations without extra
        queries.
        """

        return (
            self.db.query(DocumentChunk)
            .options(joinedload(DocumentChunk.document))
            .order_by(
                DocumentChunk.embedding.cosine_distance(embedding)
            )
            .limit(top_k)
            .all()
        )