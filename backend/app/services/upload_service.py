from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService


class UploadService:

    def __init__(
        self,
        storage: StorageService,
        pdf: PDFService,
        chunking: ChunkingService,
        embedding: EmbeddingService,
        documents: DocumentRepository,
        chunks: ChunkRepository,
    ):

        self.storage = storage
        self.pdf = pdf
        self.chunking = chunking
        self.embedding = embedding

        self.documents = documents
        self.chunks = chunks