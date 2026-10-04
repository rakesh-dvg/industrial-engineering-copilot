"""Product document upload and ingestion."""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.base import EmbeddingProvider
from app.ingest.pipeline import ingest_document_content
from app.models.document_chunk import DocumentChunk
from app.models.product_document import DocumentType, IngestStatus, ProductDocument
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.schemas.evidence import DocumentIngestResponse
from app.services.catalog import get_product_entity
from app.services.object_storage import ObjectStorageService


def _bad_request(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorResponse(error=ErrorDetail(code="BAD_REQUEST", message=message)).model_dump(),
    )


async def ingest_product_document(
    session: AsyncSession,
    product_id: UUID,
    upload: UploadFile,
    *,
    embedder: EmbeddingProvider,
    storage: ObjectStorageService,
    title: str | None = None,
) -> DocumentIngestResponse:
    product = await get_product_entity(session, product_id)
    if upload.filename is None or upload.content_type is None:
        raise _bad_request("Uploaded file must include filename and content type.")

    allowed_types = {"application/pdf", "text/plain"}
    if upload.content_type not in allowed_types:
        raise _bad_request("Only PDF and plain-text datasheets are supported in the MVP.")

    content = await upload.read()
    if not content:
        raise _bad_request("Uploaded file is empty.")

    document_id = uuid.uuid4()
    storage_key = f"datasheets/{product.model_number}/{document_id}-{upload.filename}"
    storage.upload_bytes(storage_key, content, upload.content_type)

    document = ProductDocument(
        id=document_id,
        product_id=product.id,
        document_type=DocumentType.DATASHEET,
        title=title or f"{product.model_number} Datasheet",
        filename=upload.filename,
        storage_key=storage_key,
        mime_type=upload.content_type,
        ingest_status=IngestStatus.PENDING,
    )
    session.add(document)
    await session.flush()

    await ingest_document_content(session, document, content, embedder=embedder)
    chunk_count = await session.scalar(
        select(func.count())
        .select_from(DocumentChunk)
        .where(DocumentChunk.document_id == document.id),
    )
    await session.commit()
    await session.refresh(document)

    return DocumentIngestResponse(
        document_id=document.id,
        product_id=document.product_id,
        title=document.title,
        filename=document.filename,
        mime_type=document.mime_type,
        page_count=document.page_count,
        ingest_status=document.ingest_status.value,
        chunk_count=chunk_count or 0,
    )


async def ingest_product_document_bytes(
    session: AsyncSession,
    *,
    product_id: UUID,
    title: str,
    filename: str,
    mime_type: str,
    content: bytes,
    embedder: EmbeddingProvider,
    storage: ObjectStorageService | None = None,
    commit: bool = True,
) -> ProductDocument:
    product = await get_product_entity(session, product_id)
    document_id = uuid.uuid4()
    storage_key = f"datasheets/{product.model_number}/{filename}"

    if storage is not None:
        storage.upload_bytes(storage_key, content, mime_type)

    document = ProductDocument(
        id=document_id,
        product_id=product.id,
        document_type=DocumentType.DATASHEET,
        title=title,
        filename=filename,
        storage_key=storage_key,
        mime_type=mime_type,
        ingest_status=IngestStatus.PENDING,
    )
    session.add(document)
    await session.flush()
    await ingest_document_content(session, document, content, embedder=embedder)
    if commit:
        await session.commit()
        await session.refresh(document)
    return document
