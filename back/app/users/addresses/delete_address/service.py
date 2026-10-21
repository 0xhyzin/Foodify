"""Delete an owned address after safely moving its default-address pointer."""

from app.shared.ports import UnitOfWork
from app.users.addresses.delete_address.dto import DeleteAddressCommand
from app.users.shared.guards import require_active_user, require_owned_address
from app.users.shared.interfaces import AddressRepository, UserRepository


class DeleteAddressService:
    def __init__(
        self, users: UserRepository, addresses: AddressRepository, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.addresses = addresses
        self.uow = uow

    def execute(self, command: DeleteAddressCommand) -> None:
        user = require_active_user(self.users, command.user_id, for_update=True)
        address = require_owned_address(self.addresses, command.address_id, command.user_id)
        if user.default_address_id == address.id:
            remaining = [
                existing
                for existing in self.addresses.list_for_user(command.user_id)
                if existing.id != address.id
            ]
            user.default_address_id = remaining[0].id if remaining else None
            # Move the foreign key before removing the old target row.
            self.uow.flush()
        self.addresses.delete(address)
        self.uow.commit()
