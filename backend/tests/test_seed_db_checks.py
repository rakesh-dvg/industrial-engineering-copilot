"""Seed database schema guard tests."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.seed.catalog import seed_catalog
from app.seed.db_checks import MIGRATION_REQUIRED_MESSAGE
from app.seed.followups import seed_demo_follow_ups


@pytest.mark.asyncio
async def test_catalog_seed_reports_missing_migrations(db_session: AsyncSession):
    await db_session.execute(text("DROP TABLE IF EXISTS manufacturers CASCADE"))
    await db_session.commit()

    with pytest.raises(RuntimeError, match="alembic upgrade head"):
        await seed_catalog(db_session)


@pytest.mark.asyncio
async def test_catalog_seed_missing_tables_message_is_actionable(db_session: AsyncSession):
    await db_session.execute(text("DROP TABLE IF EXISTS manufacturers CASCADE"))
    await db_session.commit()

    with pytest.raises(RuntimeError) as exc_info:
        await seed_catalog(db_session)

    message = str(exc_info.value)
    assert "alembic upgrade head" in message
    assert "manufacturers" in message
    assert MIGRATION_REQUIRED_MESSAGE.splitlines()[0] in message


@pytest.mark.asyncio
async def test_followup_seed_reports_missing_migrations(db_session: AsyncSession):
    await seed_catalog(db_session)
    await db_session.execute(text("DROP TABLE IF EXISTS sales_follow_ups CASCADE"))
    await db_session.commit()

    with pytest.raises(RuntimeError, match="sales_follow_ups"):
        await seed_demo_follow_ups(db_session)
