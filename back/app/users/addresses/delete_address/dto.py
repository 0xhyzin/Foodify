"""Internal delete command; this endpoint does not accept an HTTP body."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteAddressCommand:
    user_id: str
    address_id: str
