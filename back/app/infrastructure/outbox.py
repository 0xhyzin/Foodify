"""Transactional, encrypted email jobs. Sending happens only in the worker."""

import json
from datetime import timedelta

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.infrastructure.models import EmailOutbox
from app.shared.time import utcnow


class OutboxEmailSender:
    def __init__(self, session: Session, settings: Settings) -> None:
        self.session, self.settings = session, settings
        self.cipher = Fernet(settings.email_encryption_key.get_secret_value().encode())

    def send_action_email(self, recipient: str, purpose: str, raw_token: str) -> None:
        minutes = (
            self.settings.verification_token_minutes
            if purpose == "verify_email"
            else self.settings.reset_token_minutes
        )
        payload = json.dumps(
            {
                "recipient": recipient,
                "purpose": purpose,
                "raw_token": raw_token,
                "expires_at": (utcnow() + timedelta(minutes=minutes)).isoformat(),
            }
        )
        self.session.add(
            EmailOutbox(encrypted_payload=self.cipher.encrypt(payload.encode()).decode())
        )
