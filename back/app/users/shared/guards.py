"""Reusable ownership checks; endpoint orchestration stays in its own slice."""

from app.infrastructure.models import Address, User
from app.shared.errors import AppError
from app.users.shared.interfaces import AddressRepository, UserRepository


def require_active_user(users: UserRepository, user_id: str, for_update: bool = False) -> User:
    user = users.get_by_id(user_id, for_update=for_update)
    if user is None or not user.is_active:
        raise AppError("user_not_found", "User was not found.", 404)
    return user


def require_owned_address(
    addresses: AddressRepository, address_id: str, user_id: str, for_update: bool = False
) -> Address:
    address = addresses.get_owned(address_id, user_id, for_update=for_update)
    if address is None:
        raise AppError("address_not_found", "Address was not found.", 404)
    return address
