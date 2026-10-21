"""SMTP delivery adapter. Call from the outbox worker, never log action links."""

import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import quote

from app.core.config import Settings
from app.shared.errors import AppError


class SMTPEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        actions = {
            "verify_email": (
                "Verify your Foodify email",
                "/verify-email",
                "verify your email address",
            ),
            "password_reset": (
                "Reset your Foodify password",
                "/reset-password",
                "reset your password",
            ),
        }
        if purpose not in actions:
            raise ValueError("Unsupported email action.")
        subject, path, instruction = actions[purpose]
        # URL fragments stay out of HTTP request logs. The frontend posts this token
        # in a JSON body to the matching API action and then clears the fragment.
        link = f"{self._settings.frontend_url.rstrip('/')}{path}#token={quote(raw_token, safe='')}"
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self._settings.smtp_from_email
        message["To"] = recipient
        message.set_content(
            f"Use this link to {instruction}:\n\n{link}\n\n"
            "If you did not request this, you can ignore this email.\n"
            "Do not share this link with anyone."
        )
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
