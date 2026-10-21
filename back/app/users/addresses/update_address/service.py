"""Replace an owned address while preserving ownership and default selection."""

from app.shared.ports import UnitOfWork
from app.users.addresses.update_address.dto import UpdateAddressRequest, UpdateAddressResponse
from app.users.shared.dto.address import address_response
from app.users.shared.guards import require_active_user, require_owned_address
from app.users.shared.interfaces import AddressRepository, UserRepository


class UpdateAddressService:
    def __init__(
        self, users: UserRepository, addresses: AddressRepository, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.addresses = addresses
        self.uow = uow

    def execute(
        self, user_id: str, address_id: str, payload: UpdateAddressRequest
    ) -> UpdateAddressResponse:
        user = require_active_user(self.users, user_id, for_update=True)
        address = require_owned_address(self.addresses, address_id, user_id)
        # The request forbids extra fields, so identifiers cannot be mass assigned.
        for field, value in payload.model_dump().items():
            setattr(address, field, value)
        self.uow.commit()
        return UpdateAddressResponse.model_validate(
            address_response(address, user.default_address_id)
        )
