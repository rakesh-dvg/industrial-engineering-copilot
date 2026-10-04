"""Idempotent demo/historical sales follow-up seed for CEO dashboard demos."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.product import Product
from app.models.quotation import Quotation, QuotationLineItem, QuotationStatus
from app.models.quotation_communication import CommunicationStatus, QuotationCommunication
from app.models.sales_follow_up import FollowUpPriority, FollowUpStatus, SalesFollowUp
from app.seed.catalog import seed_catalog
from app.seed.db_checks import (
    FOLLOWUP_REQUIRED_TABLES,
    verify_required_tables,
    wrap_seed_database_errors,
)


@dataclass(frozen=True)
class DemoFollowUpSeed:
    quotation_number: str
    customer_name: str
    customer_email: str
    total: Decimal
    priority: FollowUpPriority
    notes: str = "Demo/historical sales opportunity — not a real CRM record."


DEMO_HISTORICAL_FOLLOW_UPS: tuple[DemoFollowUpSeed, ...] = (
    DemoFollowUpSeed(
        quotation_number="Q-2026-0003",
        customer_name="Apex Manufacturing",
        customer_email="procurement@apexmanufacturing.example",
        total=Decimal("8450.00"),
        priority=FollowUpPriority.P0,
    ),
    DemoFollowUpSeed(
        quotation_number="Q-2026-0002",
        customer_name="Delta Automation",
        customer_email="procurement@deltaautomation.example",
        total=Decimal("4200.00"),
        priority=FollowUpPriority.P2,
    ),
)


async def _load_demo_product(session: AsyncSession) -> Product:
    product = await session.scalar(
        select(Product)
        .options(selectinload(Product.pricing))
        .where(Product.model_number == "NS-SW-005"),
    )
    if product is None:
        raise RuntimeError("Catalog seed must run before demo follow-up seed (NS-SW-005 missing).")
    return product


async def _ensure_demo_follow_up(session: AsyncSession, seed: DemoFollowUpSeed) -> None:
    quotation = await session.scalar(
        select(Quotation)
        .options(
            selectinload(Quotation.communication),
            selectinload(Quotation.follow_up),
        )
        .where(Quotation.quotation_number == seed.quotation_number),
    )
    if quotation is not None:
        if quotation.follow_up is not None and quotation.follow_up.status == FollowUpStatus.OPEN:
            quotation.follow_up.follow_up_date = date.today()
            quotation.follow_up.priority = seed.priority
        return

    product = await _load_demo_product(session)
    pricing = product.pricing
    assert pricing is not None

    sent_at = datetime.now(tz=UTC)
    quotation = Quotation(
        id=uuid.uuid4(),
        quotation_number=seed.quotation_number,
        customer_name=seed.customer_name,
        customer_email=seed.customer_email,
        customer_reference=f"DEMO-{seed.quotation_number}",
        title="Demo historical quotation",
        currency=pricing.currency,
        status=QuotationStatus.SENT,
        validity_days=30,
        lead_time_days=pricing.lead_time_days,
        technical_status="PASS",
        subtotal=seed.total,
        discount_percent=Decimal("0"),
        discount_amount=Decimal("0.00"),
        total=seed.total,
        validation_snapshot={
            "model_number": product.model_number,
            "status": "PASS",
            "demo_historical": True,
        },
        evidence_snapshot=None,
    )
    session.add(quotation)
    await session.flush()

    session.add(
        QuotationLineItem(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            product_id=product.id,
            model_number=product.model_number,
            description=product.name,
            quantity=1,
            unit_price=seed.total,
            currency=pricing.currency,
            discount_percent=Decimal("0"),
            line_subtotal=seed.total,
            line_total=seed.total,
        ),
    )
    session.add(
        QuotationCommunication(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            customer_name=seed.customer_name,
            customer_email=seed.customer_email,
            subject=f"Quotation {seed.quotation_number} — Demo Historical",
            body=(
                f"Dear {seed.customer_name},\n\n"
                "This is a demo/historical quotation communication record. "
                "No external email was sent."
            ),
            status=CommunicationStatus.SENT,
            sent_at=sent_at,
        ),
    )
    session.add(
        SalesFollowUp(
            id=uuid.uuid4(),
            quotation_id=quotation.id,
            customer_name=seed.customer_name,
            customer_email=seed.customer_email,
            quotation_number=seed.quotation_number,
            follow_up_date=date.today(),
            priority=seed.priority,
            status=FollowUpStatus.OPEN,
            notes=seed.notes,
        ),
    )


@wrap_seed_database_errors
async def seed_demo_follow_ups(session: AsyncSession) -> None:
    """Seed demo/historical follow-ups for Apex and Delta (never duplicates ABC)."""
    await verify_required_tables(session, FOLLOWUP_REQUIRED_TABLES)

    abc_follow_up = await session.scalar(
        select(SalesFollowUp).where(SalesFollowUp.customer_name == "ABC Manufacturing"),
    )
    if abc_follow_up is not None:
        # Live workflow owns ABC Manufacturing — do not seed a second ABC opportunity.
        pass

    for seed in DEMO_HISTORICAL_FOLLOW_UPS:
        await _ensure_demo_follow_up(session, seed)

    await session.commit()


async def _main_async() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            await seed_catalog(session)
            await seed_demo_follow_ups(session)
    except RuntimeError as exc:
        print(str(exc), file=__import__("sys").stderr)
        raise SystemExit(1) from exc
    finally:
        await engine.dispose()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
