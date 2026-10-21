"""Deliver encrypted outbox jobs: APP_ENV=development python -m app.worker."""

import json
import logging
import signal
import threading
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select

from app.core.config import get_settings
from app.infrastructure.database import get_engine, get_session_factory
from app.infrastructure.email import SMTPEmailSender
from app.infrastructure.models import EmailOutbox
from app.shared.time import utcnow

logger = logging.getLogger("foodify.email_worker")
MAX_ATTEMPTS = 10


def deliver_next_email() -> bool:
    settings = get_settings()
    cipher = Fernet(settings.email_encryption_key.get_secret_value().encode())
    with get_session_factory()() as session, session.begin():
        job = session.scalar(
            select(EmailOutbox)
            .where(
                EmailOutbox.sent_at.is_(None),
                EmailOutbox.next_attempt_at <= utcnow(),
                EmailOutbox.attempts < MAX_ATTEMPTS,
            )
            .order_by(EmailOutbox.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        if job is None:
            return False
        try:
            payload = json.loads(cipher.decrypt(job.encrypted_payload.encode()))
            if datetime.fromisoformat(payload["expires_at"]) > utcnow():
                SMTPEmailSender(settings).send_action_email(
                    payload["recipient"],
                    payload["purpose"],
                    payload["raw_token"],
                )
            # Expired jobs are discarded; erase the secret after delivery/expiry.
            job.sent_at, job.encrypted_payload = utcnow(), ""
        except (InvalidToken, KeyError, ValueError, TypeError):
            job.attempts = MAX_ATTEMPTS
            logger.error("Email job cannot be decoded job_id=%s", job.id)
        except Exception as exc:
            job.attempts += 1
            job.next_attempt_at = utcnow() + timedelta(seconds=min(3600, 15 * 2**job.attempts))
            logger.warning(
                "Email delivery failed job_id=%s attempt=%s type=%s",
                job.id,
                job.attempts,
                type(exc).__name__,
            )
            if job.attempts >= MAX_ATTEMPTS:
                logger.error("Email job requires operator attention job_id=%s", job.id)
        return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    get_settings()
    try:
        while not stop.is_set():
            try:
                if not deliver_next_email():
                    stop.wait(2)
            except Exception as exc:
                logger.error("Email worker unavailable type=%s", type(exc).__name__)
                stop.wait(5)
    finally:
        get_engine().dispose()


if __name__ == "__main__":
    main()
