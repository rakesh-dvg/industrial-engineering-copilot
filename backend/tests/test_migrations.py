"""Alembic migration chain regression tests."""

import os
from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.seed.catalog import seed_catalog
from app.seed.db_checks import ALEMBIC_VERSION_MAX_LENGTH
from app.seed.followups import DEMO_HISTORICAL_FOLLOW_UPS, seed_demo_follow_ups

MIGRATION_DATABASE_URL = os.getenv(
    "MIGRATION_TEST_DATABASE_URL",
    "postgresql+psycopg://iec:iec@localhost:5432/iec_migration_fresh",
)

EXPECTED_TABLES = {
    "organizations",
    "users",
    "organization_members",
    "manufacturers",
    "product_categories",
    "products",
    "product_specifications",
    "product_pricing",
    "product_documents",
    "document_chunks",
    "quotations",
    "quotation_line_items",
    "quotation_communications",
    "sales_follow_ups",
}

EXPECTED_REVISIONS = (
    "001_initial_foundation",
    "002_product_catalog",
    "003_product_documents",
    "004_quotations",
    "005_comm_followups",
)


def test_migration_chain_order():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    revisions = [revision.revision for revision in script.walk_revisions()]
    revisions.reverse()
    assert revisions == list(EXPECTED_REVISIONS)
    assert script.get_current_head() == EXPECTED_REVISIONS[-1]


def test_revision_ids_fit_alembic_version_column():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    for revision in script.walk_revisions():
        assert len(revision.revision) <= ALEMBIC_VERSION_MAX_LENGTH, (
            f"Revision {revision.revision!r} exceeds alembic_version "
            f"VARCHAR({ALEMBIC_VERSION_MAX_LENGTH})"
        )


def test_migrations_do_not_use_metadata_create_all():
    versions_dir = Path("alembic/versions")
    for migration_file in versions_dir.glob("*.py"):
        contents = migration_file.read_text(encoding="utf-8")
        assert "create_all" not in contents, (
            f"{migration_file.name} must not call Base.metadata.create_all()"
        )
        assert "metadata.create_all" not in contents


def _recreate_migration_database() -> None:
    admin_url = os.getenv(
        "MIGRATION_TEST_ADMIN_DATABASE_URL",
        "postgresql+psycopg://iec:iec@localhost:5432/postgres",
    )
    db_name = MIGRATION_DATABASE_URL.rsplit("/", maxsplit=1)[-1]
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)
    with admin_engine.connect() as connection:
        connection.execute(
            text(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity "
                "WHERE datname = :db_name AND pid <> pg_backend_pid()",
            ),
            {"db_name": db_name},
        )
        connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin_engine.dispose()


@pytest.mark.integration
def test_fresh_database_upgrade_head(monkeypatch):
    _recreate_migration_database()

    async_url = MIGRATION_DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    monkeypatch.setenv("DATABASE_URL", async_url)
    monkeypatch.setenv("DATABASE_URL_SYNC", MIGRATION_DATABASE_URL)
    get_settings.cache_clear()

    from alembic import command

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_engine(MIGRATION_DATABASE_URL, pool_pre_ping=True)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert EXPECTED_TABLES.issubset(tables)

    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
        assert version == EXPECTED_REVISIONS[-1]

    engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_catalog_seed_succeeds_after_fresh_migration(monkeypatch):
    _recreate_migration_database()

    async_url = MIGRATION_DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    monkeypatch.setenv("DATABASE_URL", async_url)
    monkeypatch.setenv("DATABASE_URL_SYNC", MIGRATION_DATABASE_URL)
    get_settings.cache_clear()

    from alembic import command

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_async_engine(async_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        await seed_catalog(session)
        await seed_catalog(session)
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_followup_seed_succeeds_after_fresh_migration(monkeypatch):
    _recreate_migration_database()

    async_url = MIGRATION_DATABASE_URL.replace("postgresql+psycopg://", "postgresql+asyncpg://")
    monkeypatch.setenv("DATABASE_URL", async_url)
    monkeypatch.setenv("DATABASE_URL_SYNC", MIGRATION_DATABASE_URL)
    get_settings.cache_clear()

    from alembic import command

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    engine = create_async_engine(async_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as session:
        await seed_catalog(session)
        await seed_demo_follow_ups(session)
        await seed_demo_follow_ups(session)
    await engine.dispose()
    assert len(DEMO_HISTORICAL_FOLLOW_UPS) == 2
