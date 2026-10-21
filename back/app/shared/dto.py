"""Common DTO settings and the stable public error envelope."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ErrorDetail(APIModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(APIModel):
    error: ErrorDetail
