"""Complete delivery address input and output for replacement."""

from app.users.shared.dto.address import AddressResponse, AddressWriteRequest


class UpdateAddressRequest(AddressWriteRequest):
    """Full replacement fields; ownership and identifiers are never accepted."""


class UpdateAddressResponse(AddressResponse):
    """The owned address after replacement."""
