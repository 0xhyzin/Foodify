"""Email normalization and reusable secret field constraints."""

from typing import Annotated

from pydantic import EmailStr, StringConstraints, field_validator

from app.shared.dto import APIModel

Password = Annotated[str, StringConstraints(min_length=15, max_length=128)]


OpaqueToken = Annotated[
    str, StringConstraints(min_length=32, max_length=512, pattern=r"^[A-Za-z0-9_-]+$")
]


class EmailRequest(APIModel):
    email: EmailStr

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = str(value).strip().casefold()
        if len(normalized) > 254:
            raise ValueError("Email must not exceed 254 characters.")
        return normalized
