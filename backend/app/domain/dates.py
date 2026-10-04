"""Shared date helpers for deterministic, timezone-safe business dates."""

from __future__ import annotations

from datetime import UTC, date, datetime


def utc_today() -> date:
    """Calendar date in UTC — matches ``sent_at.date()`` for follow-up creation."""
    return datetime.now(tz=UTC).date()
