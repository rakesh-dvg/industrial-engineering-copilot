"""Demo email sender — records send intent without external delivery."""

from app.email.base import EmailMessage, EmailSender, EmailSendResult


class DemoEmailSender:
    provider_name = "demo"

    async def send(self, message: EmailMessage) -> EmailSendResult:
        return EmailSendResult(
            delivered=False,
            provider=self.provider_name,
            detail=(
                "Demo mode: quotation communication recorded as sent but no external "
                f"email was delivered to {message.recipient}."
            ),
        )


def get_email_sender() -> EmailSender:
    return DemoEmailSender()
