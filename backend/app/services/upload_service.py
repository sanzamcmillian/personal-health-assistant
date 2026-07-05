from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.pdf_service import PDFService
from app.services.storage_service import StorageService
from app.models.chunk import DocumentChunk
from app.models.document import Document

from fastapi import UploadFile


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

    async def process(self,
                      file: UploadFile,
                      ) -> tuple[Document, int]:
        """
        Saves the uploaded PDF, extracts text per page, chunks each page,
        embeds every chunk, and persists the Document + DocumentChunk
        rows. Returns the created Document and how many chunks it has.
        """
        filename, storage_path = await self.storage.save(file)

        document = self.documents.add(
            Document(
                filename=filename,
                original_filename=file.filename,
                mime_type=file.content_type or "application/pdf",
                storage_path=storage_path,
            )
        )

        pages = self.pdf.extract_pages(storage_path)

        chunk_count = 0

        for page_number, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue

            for text_chunk in self.chunking.split(page_text):
                if not text_chunk.content.strip():
                    continue

                embedding = self.embedding.create_embedding(
                    text_chunk.content
                )

                self.chunks.add(
                    DocumentChunk(
                        document_id=document.id,
                        page_number=page_number,
                        chunk_index=text_chunk.index,
                        content=text_chunk.content,
                        embedding=embedding,
                    )
                )

                chunk_count += 1

        return document, chunk_count