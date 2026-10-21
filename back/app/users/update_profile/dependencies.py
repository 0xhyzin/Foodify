"""Compose the update-profile operation with a shared request transaction."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.shared.dependencies import get_unit_of_work, get_user_repository
from app.users.shared.interfaces import UserRepository
from app.users.update_profile.interfaces import UpdateProfileServiceInterface
from app.users.update_profile.service import UpdateProfileService

Users = Annotated[UserRepository, Depends(get_user_repository)]
Transaction = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_service(users: Users, uow: Transaction) -> UpdateProfileServiceInterface:
    return UpdateProfileService(users, uow)
