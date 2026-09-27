"""Phase 9 DemoEmailSender unit tests."""

from unittest.mock import AsyncMock

import pytest

from app.email.base import EmailMessage, EmailSendResult
from app.email.demo_sender import DemoEmailSender, get_email_sender
from app.services.quotation_communication import (
    create_quotation_communication,
    send_quotation_to_customer,
)
from tests.test_quotation_communication import _approved_quotation, _request


@pytest.mark.asyncio
async def test_demo_email_sender_returns_not_delivered():
    sender = DemoEmailSender()
    result = await sender.send(
        EmailMessage(
            recipient="procurement@abcmanufacturing.example",
            subject="Quotation Q-2026-0001",
            body="Demo body",
        ),
    )

    assert result.delivered is False
    assert result.provider == "demo"


@pytest.mark.asyncio
async def test_demo_email_sender_includes_recipient_in_detail():
    sender = DemoEmailSender()
    recipient = "procurement@abcmanufacturing.example"
    result = await sender.send(
        EmailMessage(
            recipient=recipient,
            subject="Quotation Q-2026-0001",
            body="Demo body",
        ),
    )

    assert recipient in result.detail
    assert "no external" in result.detail.lower()


def test_get_email_sender_returns_demo_sender():
    sender = get_email_sender()
    assert isinstance(sender, DemoEmailSender)
    assert sender.provider_name == "demo"


@pytest.mark.asyncio
async def test_send_quotation_uses_injected_sender(db_session):
    quotation = await _approved_quotation(
        db_session,
        customer_email="procurement@abcmanufacturing.example",
    )
    await create_quotation_communication(db_session, quotation.id, request=_request())

    mock_sender = AsyncMock()
    mock_sender.send.return_value = EmailSendResult(
        delivered=False,
        provider="test-mock",
        detail="Mock sender recorded send without delivery.",
    )

    result = await send_quotation_to_customer(
        db_session,
        quotation.id,
        email_sender=mock_sender,
    )

    mock_sender.send.assert_awaited_once()
    assert result.demo_mode is True
    assert result.communication.status.value == "SENT"
    assert "Mock sender" in result.send_detail
