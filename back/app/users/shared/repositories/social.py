"""MySQL social persistence adapter."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import OAuthState, OAuthTicket, SocialAccount


class SqlAlchemySocialRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_account(self, provider: str, subject: str) -> SocialAccount | None:
        return self.session.scalar(
            select(SocialAccount).where(
                SocialAccount.provider == provider,
                SocialAccount.provider_subject == subject,
            )
        )

    def add_account(self, account: SocialAccount) -> None:
        self.session.add(account)

    def add_state(self, state: OAuthState) -> None:
        self.session.add(state)

    def get_state(self, state_hash: str) -> OAuthState | None:
        return self.session.scalar(
            select(OAuthState)
            .where(
                OAuthState.state_hash == state_hash,
            )
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def add_ticket(self, ticket: OAuthTicket) -> None:
        self.session.add(ticket)

    def get_ticket(self, ticket_hash: str, for_update: bool = False) -> OAuthTicket | None:
        statement = select(OAuthTicket).where(OAuthTicket.ticket_hash == ticket_hash)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(statement)
