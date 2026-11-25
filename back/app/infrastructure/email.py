"""SMTP delivery adapter. Call from the outbox worker, never log action links."""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from app.core.config import Settings
from app.infrastructure.email_content import render_action_email
from app.shared.errors import AppError

logger = logging.getLogger("foodify.email")


class SMTPEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        content = render_action_email(self._settings.frontend_url, purpose, raw_token)
        from_email = str(self._settings.smtp_from_email)
        domain = from_email.split("@")[-1] if "@" in from_email else None

        message = EmailMessage()
        message["Subject"] = content.subject
        message["From"] = formataddr((self._settings.smtp_from_name, from_email))
        message["To"] = recipient
        message["Date"] = formatdate(localtime=False)
        message["Message-ID"] = make_msgid(domain=domain)
        if self._settings.smtp_reply_to:
            message["Reply-To"] = str(self._settings.smtp_reply_to)
        message.set_content(content.text)
        message.add_alternative(content.html, subtype="html")

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
                    secret = self._settings.smtp_password.get_secret_value()
                    if self._settings.smtp_host.lower().endswith(("gmail.com", "googlemail.com")):
                        secret = "".join(secret.split())
                    connection.login(self._settings.smtp_username, secret)
                refused = connection.send_message(message)
                if refused:
                    logger.warning("SMTP refused %s recipient(s)", len(refused))
                    raise AppError(
                        "email_unavailable", "Email delivery is temporarily unavailable.", 503
                    )
        except (smtplib.SMTPException, OSError) as exc:
            logger.warning("SMTP delivery failed type=%s", type(exc).__name__)
            raise AppError(
                "email_unavailable", "Email delivery is temporarily unavailable.", 503
            ) from exc
