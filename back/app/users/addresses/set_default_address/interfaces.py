"""Set-default-address application boundary."""

from typing import Protocol

from app.users.addresses.set_default_address.dto import SetDefaultAddressResponse


class SetDefaultAddressServiceInterface(Protocol):
    def execute(self, user_id: str, address_id: str) -> SetDefaultAddressResponse: ...
