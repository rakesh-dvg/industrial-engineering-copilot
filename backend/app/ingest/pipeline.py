"""Document ingestion pipeline: extract, chunk, embed, persist."""

from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.base import EmbeddingProvider
from app.ingest.chunker import TextChunk, chunk_document_text, chunk_page_text
from app.ingest.pdf_extractor import extract_pdf_pages
from app.models.document_chunk import DocumentChunk
from app.models.product_document import IngestStatus, ProductDocument


def _chunks_from_bytes(content: bytes, mime_type: str) -> list[TextChunk]:
    if mime_type == "application/pdf":
        pages = extract_pdf_pages(content)
        chunks: list[TextChunk] = []
        next_index = 0
        for page in pages:
            for page_chunk in chunk_page_text(page):
                chunks.append(
                    TextChunk(
                        chunk_index=next_index,
                        content=page_chunk.content,
                        page_number=page_chunk.page_number,
                    ),
                )
                next_index += 1
        return chunks

    text = content.decode("utf-8")
    return chunk_document_text(text)


async def ingest_document_content(
    session: AsyncSession,
    document: ProductDocument,
    content: bytes,
    *,
    embedder: EmbeddingProvider,
) -> ProductDocument:
    document.ingest_status = IngestStatus.PROCESSING
    document.ingest_error = None
    await session.flush()

    try:
        chunks = _chunks_from_bytes(content, document.mime_type)
        if not chunks:
            raise ValueError("No extractable text found in document.")

        page_numbers = {chunk.page_number for chunk in chunks if chunk.page_number is not None}
        document.page_count = max(page_numbers) if page_numbers else None

        await session.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document.id),
        )

        embeddings = await embedder.embed_many([chunk.content for chunk in chunks])
        if len(embeddings) != len(chunks):
            raise ValueError("Embedding provider returned unexpected result count.")
        if any(len(vector) != embedder.dimensions for vector in embeddings):
            raise ValueError("Embedding dimension mismatch.")

        for chunk, vector in zip(chunks, embeddings, strict=True):
            session.add(
                DocumentChunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    product_id=document.product_id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_metadata={"source_mime_type": document.mime_type},
                    embedding=vector,
                ),
            )

        document.ingest_status = IngestStatus.COMPLETED
        document.ingest_error = None
    except Exception as exc:  # noqa: BLE001 - persist ingest failure for API visibility
        document.ingest_status = IngestStatus.FAILED
        document.ingest_error = str(exc)
        raise

    await session.flush()
    return document
