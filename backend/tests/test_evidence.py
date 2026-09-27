"""Phase 6 datasheet RAG and evidence tests."""

import io
from uuid import uuid4

import pytest
from pypdf import PdfWriter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.domain.spec_keys import SpecKey
from app.embeddings.deterministic import DeterministicEmbeddingProvider
from app.ingest.chunker import chunk_document_text, parse_page_marked_text
from app.models.document_chunk import DocumentChunk
from app.models.product import Product
from app.models.product_document import ProductDocument
from app.schemas.evidence import EvidenceStatus
from app.schemas.rfq import RequirementOperator, StructuredRequirement
from app.schemas.validation import ValidationStatus
from app.seed.catalog import seed_catalog
from app.seed.documents import seed_product_datasheets
from app.services.documents import ingest_product_document_bytes
from app.services.evidence import build_requirement_query, get_product_evidence
from app.services.retrieval import retrieve_product_chunks
from tests.test_validation import DEMO_REQUIREMENTS


@pytest.mark.asyncio
async def test_page_marked_text_parsing():
    text = "--- Page 1 ---\nLine A\n--- Page 2 ---\nLine B"
    pages = parse_page_marked_text(text)
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert "Line A" in pages[0].text
    assert pages[1].page_number == 2


def test_chunk_document_text_ordering():
    text = "--- Page 1 ---\nAlpha\n--- Page 2 ---\nBeta"
    chunks = chunk_document_text(text)
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2


@pytest.mark.asyncio
async def test_deterministic_embedding_dimensions():
    provider = DeterministicEmbeddingProvider(dimensions=384)
    vector = await provider.embed("Ethernet ports 24 VDC")
    assert len(vector) == 384
    assert abs(sum(value * value for value in vector) - 1.0) < 1e-6 or vector == [0.0] * 384


@pytest.mark.asyncio
async def test_seed_datasheet_ingestion(db_session):
    await seed_catalog(db_session)
    await seed_product_datasheets(db_session)

    documents = (await db_session.scalars(select(ProductDocument))).all()
    assert len(documents) == 3

    chunk_count = await db_session.scalar(select(func.count()).select_from(DocumentChunk))
    assert chunk_count == 9

    ns_doc = await db_session.scalar(
        select(ProductDocument)
        .join(Product)
        .where(Product.model_number == "NS-SW-005"),
    )
    assert ns_doc is not None
    assert ns_doc.page_count == 3


@pytest.mark.asyncio
async def test_retrieval_scoped_to_product(db_session):
    await seed_catalog(db_session)
    await seed_product_datasheets(db_session)
    embedder = DeterministicEmbeddingProvider()

    ns_product = await db_session.scalar(
        select(Product).where(Product.model_number == "NS-SW-005"),
    )
    vis_product = await db_session.scalar(
        select(Product).where(Product.model_number == "VIS-SW-003"),
    )
    assert ns_product and vis_product

    ns_chunks = await retrieve_product_chunks(
        db_session,
        product_id=ns_product.id,
        query="5 x Ethernet ports",
        embedder=embedder,
        top_k=1,
    )
    vis_chunks = await retrieve_product_chunks(
        db_session,
        product_id=vis_product.id,
        query="5 x Ethernet ports",
        embedder=embedder,
        top_k=1,
    )
    assert ns_chunks
    assert vis_chunks
    assert "5 x" in ns_chunks[0].text
    assert "3 x" in vis_chunks[0].text


@pytest.mark.asyncio
async def test_demo_product_evidence_results(db_session):
    await seed_catalog(db_session)
    await seed_product_datasheets(db_session)
    embedder = DeterministicEmbeddingProvider()

    async def evidence_for(model_number: str):
        product = await db_session.scalar(
            select(Product)
            .options(selectinload(Product.specifications))
            .where(Product.model_number == model_number),
        )
        assert product is not None
        return await get_product_evidence(
            db_session,
            product,
            DEMO_REQUIREMENTS,
            embedder=embedder,
        )

    pass_result = await evidence_for("NS-SW-005")
    assert pass_result.status == ValidationStatus.PASS
    ports = next(
        item for item in pass_result.requirements if item.spec_key == SpecKey.ETHERNET_PORTS
    )
    assert ports.status == ValidationStatus.PASS
    assert ports.evidence_status == EvidenceStatus.FOUND
    assert any("5 x" in item.text for item in ports.evidence)

    fail_result = await evidence_for("VIS-SW-003")
    assert fail_result.status == ValidationStatus.FAIL
    fail_ports = next(
        item for item in fail_result.requirements if item.spec_key == SpecKey.ETHERNET_PORTS
    )
    assert fail_ports.status == ValidationStatus.FAIL
    assert fail_ports.evidence_status == EvidenceStatus.FOUND
    assert any("3 x" in item.text for item in fail_ports.evidence)

    unknown_result = await evidence_for("AC-SW-008")
    assert unknown_result.status == ValidationStatus.UNKNOWN
    temp = next(
        item for item in unknown_result.requirements if item.spec_key == SpecKey.OPERATING_TEMP_MIN
    )
    assert temp.status == ValidationStatus.UNKNOWN
    assert temp.evidence_status in {EvidenceStatus.INSUFFICIENT, EvidenceStatus.FOUND}
    assert not any("-20°C to" in item.text for item in temp.evidence)


@pytest.mark.asyncio
async def test_evidence_does_not_override_validation(db_session):
    await seed_catalog(db_session)
    await seed_product_datasheets(db_session)
    product = await db_session.scalar(
        select(Product)
        .options(selectinload(Product.specifications))
        .where(Product.model_number == "VIS-SW-003"),
    )
    assert product is not None

    result = await get_product_evidence(
        db_session,
        product,
        DEMO_REQUIREMENTS,
        embedder=DeterministicEmbeddingProvider(),
    )
    assert result.status == ValidationStatus.FAIL
    for requirement in result.requirements:
        if requirement.spec_key == SpecKey.ETHERNET_PORTS:
            assert requirement.status == ValidationStatus.FAIL


@pytest.mark.asyncio
async def test_text_ingestion_records_page_count(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(select(Product).where(Product.model_number == "NS-SW-005"))
    assert product is not None

    content = b"--- Page 1 ---\nAlpha\n--- Page 2 ---\nBeta"
    document = await ingest_product_document_bytes(
        db_session,
        product_id=product.id,
        title="Two Page Datasheet",
        filename="two-page.txt",
        mime_type="text/plain",
        content=content,
        embedder=DeterministicEmbeddingProvider(),
        storage=None,
        commit=True,
    )
    assert document.page_count == 2


@pytest.mark.asyncio
async def test_pdf_ingestion_without_text_fails(db_session):
    await seed_catalog(db_session)
    product = await db_session.scalar(select(Product).where(Product.model_number == "NS-SW-005"))
    assert product is not None

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ValueError, match="No extractable text"):
        await ingest_product_document_bytes(
            db_session,
            product_id=product.id,
            title="Blank PDF",
            filename="blank.pdf",
            mime_type="application/pdf",
            content=buffer.getvalue(),
            embedder=DeterministicEmbeddingProvider(),
            storage=None,
            commit=False,
        )


@pytest.mark.asyncio
async def test_evidence_api_demo_products(seeded_client_with_documents):
    product_ids = []
    for model_number in ("NS-SW-005", "VIS-SW-003", "AC-SW-008"):
        response = await seeded_client_with_documents.get(
            "/api/v1/products",
            params={"model_number": model_number},
        )
        product_ids.append(response.json()["items"][0]["id"])

    response = await seeded_client_with_documents.post(
        "/api/v1/evidence/products",
        json={
            "product_ids": product_ids,
            "requirements": [req.model_dump(mode="json") for req in DEMO_REQUIREMENTS],
        },
    )
    assert response.status_code == 200
    statuses = {item["model_number"]: item["status"] for item in response.json()["results"]}
    assert statuses == {
        "NS-SW-005": "PASS",
        "VIS-SW-003": "FAIL",
        "AC-SW-008": "UNKNOWN",
    }


@pytest.mark.asyncio
async def test_evidence_api_single_product(seeded_client_with_documents):
    products = await seeded_client_with_documents.get(
        "/api/v1/products",
        params={"model_number": "NS-SW-005"},
    )
    product_id = products.json()["items"][0]["id"]
    response = await seeded_client_with_documents.post(
        f"/api/v1/evidence/products/{product_id}",
        json={"requirements": [DEMO_REQUIREMENTS[0].model_dump(mode="json")]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "PASS"
    assert payload["requirements"][0]["evidence"]


@pytest.mark.asyncio
async def test_evidence_api_product_not_found(seeded_client_with_documents):
    response = await seeded_client_with_documents.post(
        f"/api/v1/evidence/products/{uuid4()}",
        json={"requirements": [DEMO_REQUIREMENTS[0].model_dump(mode="json")]},
    )
    assert response.status_code == 404


def test_build_requirement_query_includes_source_text():
    requirement = StructuredRequirement(
        spec_key=SpecKey.ETHERNET_PORTS,
        operator=RequirementOperator.GTE,
        value=5,
        source_text="minimum 5 Ethernet ports",
    )
    query = build_requirement_query(requirement)
    assert "Ethernet ports" in query
    assert "minimum 5 Ethernet ports" in query
