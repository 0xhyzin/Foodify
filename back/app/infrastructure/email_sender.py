"""Composition root for email adapters; workers depend on the EmailSender port."""

from app.core.config import Settings
from app.infrastructure.brevo_email import BrevoEmailSender
from app.infrastructure.email import SMTPEmailSender
from app.infrastructure.resend_email import ResendEmailSender
from app.shared.ports import EmailSender


def create_email_sender(settings: Settings) -> EmailSender:
    if settings.email_provider == "brevo":
        return BrevoEmailSender(settings)
    if settings.email_provider == "resend":
        return ResendEmailSender(settings)
    return SMTPEmailSender(settings)
