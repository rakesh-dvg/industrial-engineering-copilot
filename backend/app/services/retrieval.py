"""Semantic chunk retrieval using PostgreSQL + pgvector."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.base import EmbeddingProvider
from app.models.document_chunk import DocumentChunk
from app.models.product_document import ProductDocument


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    product_id: UUID
    text: str
    page_number: int | None
    document_title: str
    document_filename: str
    similarity_score: float


async def retrieve_product_chunks(
    session: AsyncSession,
    *,
    product_id: UUID,
    query: str,
    embedder: EmbeddingProvider,
    top_k: int = 3,
) -> list[RetrievedChunk]:
    if top_k < 1:
        return []

    query_vector = await embedder.embed(query)
    distance_expr = DocumentChunk.embedding.cosine_distance(query_vector).label("distance")

    rows = await session.execute(
        select(DocumentChunk, ProductDocument, distance_expr)
        .join(ProductDocument, ProductDocument.id == DocumentChunk.document_id)
        .where(DocumentChunk.product_id == product_id)
        .order_by(distance_expr)
        .limit(top_k),
    )

    results: list[RetrievedChunk] = []
    for chunk, document, distance in rows.all():
        similarity = max(0.0, 1.0 - float(distance))
        results.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=document.id,
                product_id=chunk.product_id,
                text=chunk.content,
                page_number=chunk.page_number,
                document_title=document.title,
                document_filename=document.filename,
                similarity_score=similarity,
            ),
        )
    return results
