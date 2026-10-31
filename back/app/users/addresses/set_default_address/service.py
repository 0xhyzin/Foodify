"""Choose a default address belonging to the active customer."""

from app.shared.ports import UnitOfWork
from app.users.addresses.set_default_address.dto import SetDefaultAddressResponse
from app.users.shared.dto.profile import user_response
from app.users.shared.guards import require_active_user, require_owned_address
from app.users.shared.interfaces import AddressRepository, UserRepository


class SetDefaultAddressService:
    def __init__(
        self, users: UserRepository, addresses: AddressRepository, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.addresses = addresses
        self.uow = uow

    def execute(self, user_id: str, address_id: str) -> SetDefaultAddressResponse:
        user = require_active_user(self.users, user_id, for_update=True)
        address = require_owned_address(self.addresses, address_id, user_id, for_update=True)
        user.default_address_id = address.id
        self.uow.commit()
        return SetDefaultAddressResponse.model_validate(user_response(user))
