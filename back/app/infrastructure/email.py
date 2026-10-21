"""SMTP delivery adapter. Call from the outbox worker, never log action links."""

import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import Settings
from app.infrastructure.email_content import render_action_email
from app.shared.errors import AppError


class SMTPEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        content = render_action_email(self._settings.frontend_url, purpose, raw_token)
        message = EmailMessage()
        message["Subject"] = content.subject
        message["From"] = self._settings.smtp_from_email
        message["To"] = recipient
        message.set_content(content.text)
        context = ssl.create_default_context()
        try:
            if self._settings.smtp_use_ssl:
                connection = smtplib.SMTP_SSL(
                    self._settings.smtp_host,
                    self._settings.smtp_port,
                    timeout=self._settings.smtp_timeout_seconds,
                    context=context,
                )
            else:
                connection = smtplib.SMTP(
                    self._settings.smtp_host,
                    self._settings.smtp_port,
                    timeout=self._settings.smtp_timeout_seconds,
                )
            with connection:
                connection.ehlo()
                if self._settings.smtp_use_tls:
                    connection.starttls(context=context)
                    connection.ehlo()
                if self._settings.smtp_username and self._settings.smtp_password:
                    connection.login(
                        self._settings.smtp_username,
                        self._settings.smtp_password.get_secret_value(),
                    )
                connection.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise AppError(
                "email_unavailable", "Email delivery is temporarily unavailable.", 503
            ) from exc
