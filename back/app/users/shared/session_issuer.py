"""Create persistent sessions and issue access/refresh token pairs."""

from datetime import timedelta

from app.infrastructure.models import AuthSession, RefreshToken, User, new_id
from app.shared.ports import TokenCodec, UnitOfWork
from app.shared.time import utcnow
from app.shared.tokens import generate_token, hash_token
from app.users.shared.dto.profile import user_response
from app.users.shared.dto.tokens import TokenResponse
from app.users.shared.interfaces import SessionRepository


class SessionIssuer:
    def __init__(
        self,
        sessions: SessionRepository,
        tokens: TokenCodec,
        uow: UnitOfWork,
        refresh_days: int,
    ) -> None:
        self.sessions = sessions
        self.tokens = tokens
        self.uow = uow
        self.refresh_days = refresh_days

    def create_session(self, user: User) -> TokenResponse:
        """The calling use case holds the user lock and commits the transaction."""
        session = AuthSession(
            id=new_id(),
            user_id=user.id,
            created_at=utcnow(),
            expires_at=utcnow() + timedelta(days=self.refresh_days),
        )
        self.sessions.add(session)
        self.uow.flush()
        return self.issue_token_pair(user, session)

    def issue_token_pair(self, user: User, session: AuthSession) -> TokenResponse:
        """Persist only the refresh token digest; return the raw token once."""
        refresh = generate_token()
        self.sessions.add_refresh(
            RefreshToken(
                id=new_id(),
                session_id=session.id,
                token_hash=hash_token(refresh),
                created_at=utcnow(),
            )
        )
        access, seconds = self.tokens.encode_access(user.id, session.id)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=seconds,
            user=user_response(user),
        )
