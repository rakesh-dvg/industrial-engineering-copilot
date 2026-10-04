"""Seed demo product datasheets for Phase 6 evidence."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.embeddings.deps import get_embedding_provider
from app.models.product import Product
from app.models.product_document import ProductDocument
from app.services.documents import ingest_product_document_bytes

DATASHEET_DIR = Path(__file__).resolve().parent / "datasheets"

DEMO_DATASHEETS: tuple[tuple[str, str], ...] = (
    ("NS-SW-005", "NS-SW-005-datasheet.txt"),
    ("VIS-SW-003", "VIS-SW-003-datasheet.txt"),
    ("AC-SW-008", "AC-SW-008-datasheet.txt"),
)


async def seed_product_datasheets(session: AsyncSession) -> None:
    embedder = get_embedding_provider()
    for model_number, filename in DEMO_DATASHEETS:
        product = await session.scalar(
            select(Product).where(Product.model_number == model_number),
        )
        if product is None:
            continue

        existing = await session.scalar(
            select(ProductDocument).where(
                ProductDocument.product_id == product.id,
                ProductDocument.filename == filename,
            ),
        )
        if existing is not None:
            continue

        content = (DATASHEET_DIR / filename).read_bytes()
        await ingest_product_document_bytes(
            session,
            product_id=product.id,
            title=f"{model_number} Datasheet",
            filename=filename,
            mime_type="text/plain",
            content=content,
            embedder=embedder,
            storage=None,
            commit=False,
        )
    await session.commit()


async def _main_async() -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.config import get_settings
    from app.seed.catalog import seed_catalog

    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed_catalog(session)
        await seed_product_datasheets(session)
    await engine.dispose()


def main() -> None:
    import asyncio

    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
