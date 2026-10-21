"""Compose the get-profile operation from its repository boundary."""

from typing import Annotated

from fastapi import Depends

from app.users.get_profile.interfaces import GetProfileServiceInterface
from app.users.get_profile.service import GetProfileService
from app.users.shared.dependencies import get_user_repository
from app.users.shared.interfaces import UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]


def get_service(users: Users) -> GetProfileServiceInterface:
    return GetProfileService(users)
