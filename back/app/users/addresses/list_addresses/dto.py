"""Response for one address returned by the list-addresses operation."""

from app.users.shared.dto.address import AddressResponse


class ListAddressesResponse(AddressResponse):
    """An owned delivery address with its current default status."""
