"""Update-address application boundary."""

from typing import Protocol

from app.users.addresses.update_address.dto import UpdateAddressRequest, UpdateAddressResponse


class UpdateAddressServiceInterface(Protocol):
    def execute(
        self, user_id: str, address_id: str, payload: UpdateAddressRequest
    ) -> UpdateAddressResponse: ...
