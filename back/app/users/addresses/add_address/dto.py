"""Delivery address input and output owned by the add-address operation."""

from app.users.shared.dto.address import AddressResponse, AddressWriteRequest


class AddAddressRequest(AddressWriteRequest):
    """Validated delivery fields for a new owned address."""


class AddAddressResponse(AddressResponse):
    """The created delivery address and its default status."""
