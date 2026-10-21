"""Read the customer's addresses in repository creation order."""

from app.users.addresses.list_addresses.dto import ListAddressesResponse
from app.users.shared.dto.address import address_response
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import AddressRepository, UserRepository


class ListAddressesService:
    def __init__(self, users: UserRepository, addresses: AddressRepository) -> None:
        self.users = users
        self.addresses = addresses

    def execute(self, user_id: str) -> list[ListAddressesResponse]:
        user = require_active_user(self.users, user_id)
        return [
            ListAddressesResponse.model_validate(address_response(address, user.default_address_id))
            for address in self.addresses.list_for_user(user_id)
        ]
