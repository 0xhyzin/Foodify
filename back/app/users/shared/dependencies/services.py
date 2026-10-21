"""Factories for reusable token policies, separate from operation factories."""

from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.shared.ports import EmailSender, TokenCodec, UnitOfWork
from app.users.shared.access_authenticator import AccessAuthenticator
from app.users.shared.dependencies.repositories import (
    get_action_repository,
    get_session_repository,
    get_user_repository,
)
from app.users.shared.dependencies.resources import (
    get_email_sender,
    get_token_codec,
    get_unit_of_work,
)
from app.users.shared.email_actions import EmailActionService
from app.users.shared.interfaces import (
    AccessAuthenticatorInterface,
    ActionTokenRepository,
    EmailActionServiceInterface,
    SessionIssuerInterface,
    SessionRepository,
    UserRepository,
)
from app.users.shared.session_issuer import SessionIssuer


def get_session_issuer(
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    tokens: Annotated[TokenCodec, Depends(get_token_codec)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> SessionIssuerInterface:
    return SessionIssuer(sessions, tokens, uow, get_settings().refresh_token_days)


def get_access_authenticator(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    tokens: Annotated[TokenCodec, Depends(get_token_codec)],
) -> AccessAuthenticatorInterface:
    return AccessAuthenticator(users, sessions, tokens)


def get_email_actions(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    actions: Annotated[ActionTokenRepository, Depends(get_action_repository)],
    sender: Annotated[EmailSender, Depends(get_email_sender)],
) -> EmailActionServiceInterface:
    settings = get_settings()
    return EmailActionService(
        users, actions, sender, settings.verification_token_minutes, settings.reset_token_minutes
    )
