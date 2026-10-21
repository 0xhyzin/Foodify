"""List-addresses application boundary."""

from typing import Protocol

from app.users.addresses.list_addresses.dto import ListAddressesResponse


class ListAddressesServiceInterface(Protocol):
    def execute(self, user_id: str) -> list[ListAddressesResponse]: ...
