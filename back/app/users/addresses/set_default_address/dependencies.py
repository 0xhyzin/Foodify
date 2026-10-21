"""Compose default-address selection with the request transaction."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.addresses.set_default_address.interfaces import SetDefaultAddressServiceInterface
from app.users.addresses.set_default_address.service import SetDefaultAddressService
from app.users.shared.dependencies import (
    get_address_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import AddressRepository, UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]
Addresses = Annotated[AddressRepository, Depends(get_address_repository)]
Transaction = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_service(
    users: Users, addresses: Addresses, uow: Transaction
) -> SetDefaultAddressServiceInterface:
    return SetDefaultAddressService(users, addresses, uow)
