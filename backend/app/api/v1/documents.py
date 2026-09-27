from uuid import UUID

from fastapi import APIRouter, File, Form, UploadFile

from app.auth.deps import DbSession
from app.embeddings.deps import get_embedding_provider
from app.schemas.evidence import DocumentIngestResponse
from app.services.documents import ingest_product_document
from app.services.object_storage import get_object_storage

router = APIRouter(tags=["Documents"])


@router.post(
    "/documents/products/{product_id}/ingest",
    response_model=DocumentIngestResponse,
)
async def ingest_product_datasheet(
    session: DbSession,
    product_id: UUID,
    file: UploadFile = File(...),  # noqa: B008
    title: str | None = Form(default=None),
) -> DocumentIngestResponse:
    return await ingest_product_document(
        session,
        product_id,
        file,
        embedder=get_embedding_provider(),
        storage=get_object_storage(),
        title=title,
    )
