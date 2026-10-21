"""Add-address application boundary."""

from typing import Protocol

from app.users.addresses.add_address.dto import AddAddressRequest, AddAddressResponse


class AddAddressServiceInterface(Protocol):
    def execute(self, user_id: str, payload: AddAddressRequest) -> AddAddressResponse: ...
