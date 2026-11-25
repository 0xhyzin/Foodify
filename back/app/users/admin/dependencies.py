"""Dependency wiring for Admin staff/user endpoints."""

from typing import Annotated

from fastapi import Depends

from app.ordering.shared.dependencies import Catalog, Staff
from app.shared.ports import PasswordHasher, UnitOfWork
from app.users.shared.dependencies import (
    DB,
    get_password_hasher,
    get_session_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import SessionRepository, UserRepository

from .interfaces import AdminUsersServiceInterface
from .repository import SqlAlchemyAdminDirectoryRepository
from .service import AdminUsersService


def get_service(
    db: DB,
    catalog: Catalog,
    staff: Staff,
    users: Annotated[UserRepository, Depends(get_user_repository)],
    sessions: Annotated[SessionRepository, Depends(get_session_repository)],
    hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    uow: Annotated[UnitOfWork, Depends(get_unit_of_work)],
) -> AdminUsersServiceInterface:
    return AdminUsersService(
        users=users,
        directory=SqlAlchemyAdminDirectoryRepository(db),
        catalog=catalog,
        staff=staff,
        sessions=sessions,
        hasher=hasher,
        uow=uow,
    )
