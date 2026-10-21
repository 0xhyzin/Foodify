"""Preview or prune expired authentication records after a retention period."""

import argparse
from datetime import timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.database import get_session_factory
from app.infrastructure.models import (
    ActionToken,
    AuthSession,
    EmailOutbox,
    OAuthState,
    OAuthTicket,
    RefreshToken,
)
from app.shared.time import utcnow


def prune_retained_records(session: Session, days_retention: int, apply: bool) -> dict[str, int]:
    """Preserve live-session refresh history needed to detect token replay."""
    if days_retention < 1:
        raise ValueError("Retention must be at least one day.")
    cutoff = utcnow() - timedelta(days=days_retention)
    session_condition = or_(
        AuthSession.expires_at <= cutoff,
        AuthSession.revoked_at <= cutoff,
    )
    candidates = (
        (EmailOutbox, EmailOutbox.sent_at <= cutoff),
        (OAuthState, or_(OAuthState.expires_at <= cutoff, OAuthState.consumed_at <= cutoff)),
        (OAuthTicket, or_(OAuthTicket.expires_at <= cutoff, OAuthTicket.consumed_at <= cutoff)),
        (ActionToken, or_(ActionToken.expires_at <= cutoff, ActionToken.consumed_at <= cutoff)),
        (AuthSession, session_condition),
    )
    counts = {
        model.__tablename__: int(
            session.scalar(select(func.count()).select_from(model).where(condition)) or 0
        )
        for model, condition in candidates
    }
    counts["refresh_tokens_cascaded"] = int(
        session.scalar(
            select(func.count())
            .select_from(RefreshToken)
            .join(AuthSession, RefreshToken.session_id == AuthSession.id)
            .where(session_condition)
        )
        or 0
    )
    if apply:
        for model, condition in candidates:
            session.execute(
                delete(model).where(condition).execution_options(synchronize_session=False)
            )
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days-retention", type=int, default=30)
    parser.add_argument(
        "--apply", action="store_true", help="Delete candidates; default only prints counts."
    )
    arguments = parser.parse_args()
    if arguments.days_retention < 1:
        parser.error("--days-retention must be at least 1.")
    settings = get_settings()
    try:
        with get_session_factory()() as session, session.begin():
            counts = prune_retained_records(session, arguments.days_retention, arguments.apply)
    except SQLAlchemyError:
        raise SystemExit(
            "Cleanup could not be completed. Check database availability and migrations."
        ) from None
    mode = "Applied cleanup" if arguments.apply else "Preview only; no rows deleted"
    print(f"{mode} (environment={settings.app_env}, retention_days={arguments.days_retention}).")
    for table, count in counts.items():
        print(f"{table}: {count}")


if __name__ == "__main__":
    main()
