"""Create an owned delivery address with serialized default selection."""

from uuid import uuid4

from app.infrastructure.models import Address
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.addresses.add_address.dto import AddAddressRequest, AddAddressResponse
from app.users.shared.dto.address import address_response
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import AddressRepository, UserRepository

MAX_ADDRESSES_PER_USER = 20


class AddAddressService:
    def __init__(
        self, users: UserRepository, addresses: AddressRepository, uow: UnitOfWork
    ) -> None:
        self.users = users
        self.addresses = addresses
        self.uow = uow

    def execute(self, user_id: str, payload: AddAddressRequest) -> AddAddressResponse:
        # Lock the parent before address mutations to serialize the limit and default.
        user = require_active_user(self.users, user_id, for_update=True)
        if len(self.addresses.list_for_user(user_id, for_update=True)) >= MAX_ADDRESSES_PER_USER:
            raise AppError(
                "address_limit_reached",
                f"A profile can have up to {MAX_ADDRESSES_PER_USER} addresses.",
                409,
            )
        address = Address(
            id=str(uuid4()),
            user_id=user_id,
            created_at=utcnow(),
            **payload.model_dump(),
        )
        self.addresses.add(address)
        # The target row must exist before the default-address foreign key is updated.
        self.uow.flush()
        if user.default_address_id is None:
            user.default_address_id = address.id
        self.uow.commit()
        return AddAddressResponse.model_validate(address_response(address, user.default_address_id))
