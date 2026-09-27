"""Demo sales follow-up seed tests."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models.quotation import Quotation
from app.models.sales_follow_up import FollowUpStatus, SalesFollowUp
from app.seed.catalog import seed_catalog
from app.seed.followups import DEMO_HISTORICAL_FOLLOW_UPS, seed_demo_follow_ups
from app.services.quotations import _next_quotation_number


@pytest.mark.asyncio
async def test_demo_follow_up_seed_is_idempotent(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)
    first_count = await db_session.scalar(select(func.count()).select_from(SalesFollowUp))

    await seed_demo_follow_ups(db_session)
    second_count = await db_session.scalar(select(func.count()).select_from(SalesFollowUp))
    assert second_count == first_count == len(DEMO_HISTORICAL_FOLLOW_UPS)


@pytest.mark.asyncio
async def test_demo_follow_up_seed_creates_historical_opportunities(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)

    follow_ups = (
        await db_session.scalars(
            select(SalesFollowUp).order_by(SalesFollowUp.quotation_number.asc()),
        )
    ).all()
    assert len(follow_ups) == 2

    by_customer = {item.customer_name: item for item in follow_ups}
    assert str(by_customer["Apex Manufacturing"].priority) == "P0"
    assert by_customer["Apex Manufacturing"].quotation_number == "Q-2026-0003"
    assert str(by_customer["Delta Automation"].priority) == "P2"
    assert by_customer["Delta Automation"].quotation_number == "Q-2026-0002"
    assert all(item.status == FollowUpStatus.OPEN for item in follow_ups)
    assert all(item.follow_up_date == date.today() for item in follow_ups)


@pytest.mark.asyncio
async def test_demo_follow_up_seed_does_not_create_abc(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)

    abc_count = await db_session.scalar(
        select(func.count())
        .select_from(SalesFollowUp)
        .where(SalesFollowUp.customer_name == "ABC Manufacturing"),
    )
    assert abc_count == 0


@pytest.mark.asyncio
async def test_demo_follow_up_seed_does_not_duplicate_existing_abc(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)

    from datetime import UTC, datetime
    from uuid import uuid4

    from app.models.quotation import QuotationStatus
    from app.models.quotation_communication import CommunicationStatus, QuotationCommunication
    from app.models.sales_follow_up import FollowUpPriority

    abc_quotation = Quotation(
        id=uuid4(),
        quotation_number="Q-2026-0001",
        customer_name="ABC Manufacturing",
        customer_email="procurement@abcmanufacturing.example",
        currency="USD",
        status=QuotationStatus.SENT,
        validity_days=30,
        lead_time_days=14,
        technical_status="PASS",
        subtotal=Decimal("1850.00"),
        discount_percent=Decimal("0"),
        discount_amount=Decimal("0.00"),
        total=Decimal("1850.00"),
        validation_snapshot={"status": "PASS", "demo_historical": False},
    )
    db_session.add(abc_quotation)
    await db_session.flush()
    db_session.add(
        QuotationCommunication(
            id=uuid4(),
            quotation_id=abc_quotation.id,
            customer_name="ABC Manufacturing",
            customer_email="procurement@abcmanufacturing.example",
            subject="Quotation Q-2026-0001",
            body="Live workflow demo quotation.",
            status=CommunicationStatus.SENT,
            sent_at=datetime.now(tz=UTC),
        ),
    )
    db_session.add(
        SalesFollowUp(
            id=uuid4(),
            quotation_id=abc_quotation.id,
            customer_name="ABC Manufacturing",
            customer_email="procurement@abcmanufacturing.example",
            quotation_number="Q-2026-0001",
            follow_up_date=date.today(),
            priority=FollowUpPriority.P1,
            status=FollowUpStatus.OPEN,
        ),
    )
    await db_session.commit()

    await seed_demo_follow_ups(db_session)
    abc_count = await db_session.scalar(
        select(func.count())
        .select_from(SalesFollowUp)
        .where(SalesFollowUp.customer_name == "ABC Manufacturing"),
    )
    assert abc_count == 1


@pytest.mark.asyncio
async def test_demo_follow_up_quotation_totals(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)

    totals = {
        row.quotation_number: row.total
        for row in await db_session.scalars(
            select(Quotation).where(
                Quotation.quotation_number.in_(["Q-2026-0002", "Q-2026-0003"]),
            ),
        )
    }
    assert totals["Q-2026-0003"] == Decimal("8450.00")
    assert totals["Q-2026-0002"] == Decimal("4200.00")


@pytest.mark.asyncio
async def test_next_quotation_number_fills_gaps(db_session):
    await seed_catalog(db_session)
    await seed_demo_follow_ups(db_session)

    next_number = await _next_quotation_number(db_session)
    assert next_number == "Q-2026-0001"
