"""Shared address fields and public response mapping."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import Field, StringConstraints, model_validator

from app.infrastructure.models import Address
from app.shared.dto import APIModel
from app.users.shared.dto.primitives import PersonName, PhoneNumber, ShortText
from app.users.shared.dto.profile import _as_utc


class AddressWriteRequest(APIModel):
    label: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
    ]
    recipient_name: PersonName
    phone: PhoneNumber
    country_code: Annotated[
        str,
        StringConstraints(strip_whitespace=True, to_upper=True, pattern=r"^[A-Za-z]{2}$"),
    ] = Field(description="Two-letter ISO 3166-1 country code, e.g. EG.")
    city: ShortText
    area: ShortText
    street: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
    ]
    building: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
    ]
    floor: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
        ]
        | None
    ) = None
    apartment: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=30),
        ]
        | None
    ) = None
    delivery_notes: (
        Annotated[
            str,
            StringConstraints(strip_whitespace=True, min_length=1, max_length=500),
        ]
        | None
    ) = None
    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
        max_digits=10,
        decimal_places=7,
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
        max_digits=10,
        decimal_places=7,
    )

    @model_validator(mode="after")
    def require_coordinate_pair(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude and longitude must be supplied together.")
        return self


class AddressResponse(AddressWriteRequest):
    id: str
    is_default: bool
    created_at: datetime


def address_response(address: Address, default_address_id: str | None) -> AddressResponse:
    return AddressResponse(
        id=address.id,
        label=address.label,
        recipient_name=address.recipient_name,
        phone=address.phone,
        country_code=address.country_code,
        city=address.city,
        area=address.area,
        street=address.street,
        building=address.building,
        floor=address.floor,
        apartment=address.apartment,
        delivery_notes=address.delivery_notes,
        latitude=address.latitude,
        longitude=address.longitude,
        is_default=address.id == default_address_id,
        created_at=_as_utc(address.created_at),
    )
