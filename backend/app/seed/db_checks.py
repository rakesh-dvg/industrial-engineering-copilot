"""Database schema checks for seed commands.

Seed scripts do not run Alembic migrations. They verify required tables exist
and raise a clear developer-facing error when migrations have not been applied.
"""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MIGRATION_REQUIRED_MESSAGE = (
    "Required database tables are missing. Run Alembic migrations before seeding:\n\n"
    "  cd backend\n"
    "  alembic upgrade head\n\n"
    "Then rerun the seed command."
)

CATALOG_REQUIRED_TABLES: frozenset[str] = frozenset(
    {
        "manufacturers",
        "product_categories",
        "products",
        "product_specifications",
        "product_pricing",
    },
)

FOLLOWUP_REQUIRED_TABLES: frozenset[str] = CATALOG_REQUIRED_TABLES | frozenset(
    {
        "quotations",
        "quotation_line_items",
        "quotation_communications",
        "sales_follow_ups",
    },
)

ALEMBIC_VERSION_MAX_LENGTH = 32


def format_missing_tables_error(missing_tables: Iterable[str]) -> str:
    tables = ", ".join(sorted(missing_tables))
    return (
        f"{MIGRATION_REQUIRED_MESSAGE}\n"
        f"Missing tables: {tables}"
    )


async def find_missing_tables(session: AsyncSession, required_tables: Iterable[str]) -> set[str]:
    result = await session.execute(
        text(
            "SELECT table_name "
            "FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = ANY(:names)",
        ),
        {"names": list(required_tables)},
    )
    present = {row[0] for row in result}
    return set(required_tables) - present


async def verify_required_tables(session: AsyncSession, required_tables: Iterable[str]) -> None:
    missing = await find_missing_tables(session, required_tables)
    if missing:
        raise RuntimeError(format_missing_tables_error(missing))


def wrap_seed_database_errors(func):
    """Convert missing-table database errors into migration guidance."""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except RuntimeError:
            raise
        except Exception as exc:
            if _is_missing_table_error(exc):
                missing_table = _extract_missing_table_name(exc)
                if missing_table:
                    raise RuntimeError(
                        format_missing_tables_error([missing_table]),
                    ) from exc
                raise RuntimeError(MIGRATION_REQUIRED_MESSAGE) from exc
            raise

    return wrapper


def _is_missing_table_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    if "undefinedtableerror" in message or "does not exist" in message:
        return True
    cause = exc.__cause__
    return cause is not None and _is_missing_table_error(cause)


def _extract_missing_table_name(exc: BaseException) -> str | None:
    message = str(exc)
    marker = 'relation "'
    if marker not in message:
        cause = exc.__cause__
        if cause is not None:
            return _extract_missing_table_name(cause)
        return None
    start = message.index(marker) + len(marker)
    end = message.find('"', start)
    if end == -1:
        return None
    return message[start:end]
