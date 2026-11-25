"""HTTPS action-email adapter for Resend API."""

import logging
from email.utils import formataddr

import httpx

from app.core.config import Settings
from app.infrastructure.email_content import render_action_email
from app.shared.errors import AppError

logger = logging.getLogger("foodify.email")


class ResendEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        key = self._settings.resend_api_key
        if not key:
            raise AppError("email_unavailable", "Email delivery is temporarily unavailable.", 503)
        content = render_action_email(self._settings.frontend_url, purpose, raw_token)
        sender = formataddr(
            (self._settings.smtp_from_name, str(self._settings.smtp_from_email))
        )
        payload: dict[str, object] = {
            "from": sender,
            "to": [recipient],
            "subject": content.subject,
            "text": content.text,
            "html": content.html,
        }
        if self._settings.smtp_reply_to:
            payload["reply_to"] = str(self._settings.smtp_reply_to)
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {key.get_secret_value()}",
                    "Accept": "application/json",
                },
                json=payload,
                timeout=self._settings.smtp_timeout_seconds,
                follow_redirects=False,
            )
            if response.status_code not in {200, 201}:
                logger.warning("Resend email rejected status=%s", response.status_code)
                raise AppError(
                    "email_unavailable", "Email delivery is temporarily unavailable.", 503
                )
        except httpx.HTTPError as exc:
            logger.warning("Resend delivery failed type=%s", type(exc).__name__)
            raise AppError(
                "email_unavailable", "Email delivery is temporarily unavailable.", 503
            ) from exc
