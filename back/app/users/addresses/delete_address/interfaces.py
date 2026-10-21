"""Delete-address application boundary."""

from typing import Protocol

from app.users.addresses.delete_address.dto import DeleteAddressCommand


class DeleteAddressServiceInterface(Protocol):
    def execute(self, command: DeleteAddressCommand) -> None: ...
