"""Email sender abstraction for quotation communications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class EmailMessage:
    recipient: str
    subject: str
    body: str
    attachment_name: str | None = None


@dataclass(frozen=True)
class EmailSendResult:
    delivered: bool
    provider: str
    detail: str


class EmailSender(Protocol):
    async def send(self, message: EmailMessage) -> EmailSendResult: ...
