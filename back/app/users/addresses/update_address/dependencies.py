"""Compose update-address with request-scoped persistence and transaction boundaries."""

from typing import Annotated

from fastapi import Depends

from app.shared.ports import UnitOfWork
from app.users.addresses.update_address.interfaces import UpdateAddressServiceInterface
from app.users.addresses.update_address.service import UpdateAddressService
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
) -> UpdateAddressServiceInterface:
    return UpdateAddressService(users, addresses, uow)
