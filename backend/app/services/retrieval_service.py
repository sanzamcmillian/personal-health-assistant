from app.models.chunk import DocumentChunk
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    """
    Embeds a question and retrieves the most relevant document chunks
    to use as context for answering it.
    """

    def __init__(
        self,
        embedding: EmbeddingService,
        chunks: ChunkRepository,
    ):
        self.embedding = embedding
        self.chunks = chunks

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[DocumentChunk]:
        query_embedding = self.embedding.create_embedding(question)

        return self.chunks.similarity_search(
            embedding=query_embedding,
            top_k=top_k,
        )