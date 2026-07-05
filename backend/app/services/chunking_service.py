from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    content: str


class ChunkingService:

    @staticmethod
    def split(
        text: str,
        chunk_size: int = 800,
        overlap: int = 150,
    ) -> list[TextChunk]:

        chunks = []

        start = 0

        index = 0

        while start < len(text):

            end = start + chunk_size

            chunk = text[start:end]

            chunks.append(
                TextChunk(
                    index=index,
                    content=chunk,
                )
            )

            index += 1

            start += (
                chunk_size - overlap
            )

        return chunks