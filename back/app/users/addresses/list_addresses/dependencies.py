"""Compose list-addresses with the customer and address repositories."""

from typing import Annotated

from fastapi import Depends

from app.users.addresses.list_addresses.interfaces import ListAddressesServiceInterface
from app.users.addresses.list_addresses.service import ListAddressesService
from app.users.shared.dependencies import get_address_repository, get_user_repository
from app.users.shared.interfaces import AddressRepository, UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]
Addresses = Annotated[AddressRepository, Depends(get_address_repository)]


def get_service(users: Users, addresses: Addresses) -> ListAddressesServiceInterface:
    return ListAddressesService(users, addresses)
