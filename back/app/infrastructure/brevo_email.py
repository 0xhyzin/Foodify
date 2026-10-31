"""HTTPS action-email adapter for hosts that block outgoing SMTP ports."""

import httpx

from app.core.config import Settings
from app.infrastructure.email_content import render_action_email
from app.shared.errors import AppError


class BrevoEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        key = self._settings.brevo_api_key
        if not key:
            raise AppError("email_unavailable", "Email delivery is temporarily unavailable.", 503)
        content = render_action_email(self._settings.frontend_url, purpose, raw_token)
        try:
            response = httpx.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={"api-key": key.get_secret_value(), "accept": "application/json"},
                json={
                    "sender": {"name": "Foodify", "email": str(self._settings.smtp_from_email)},
                    "to": [{"email": recipient}],
                    "subject": content.subject,
                    "textContent": content.text,
                },
                timeout=self._settings.smtp_timeout_seconds,
                follow_redirects=False,
            )
            if response.status_code != 201:
                raise AppError(
                    "email_unavailable", "Email delivery is temporarily unavailable.", 503
                )
        except httpx.HTTPError as exc:
            # Provider bodies and request contents can contain private data.
            raise AppError(
                "email_unavailable", "Email delivery is temporarily unavailable.", 503
            ) from exc
