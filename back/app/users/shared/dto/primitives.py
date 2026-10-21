"""Reusable scalar constraints for customer DTOs."""

from typing import Annotated

from pydantic import StringConstraints

PhoneNumber = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^\+[1-9][0-9]{7,14}$"),
]


PersonName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]


ShortText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]
