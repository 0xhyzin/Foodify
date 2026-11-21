"""DTO contracts for kitchen preparer order updates."""

from typing import Literal

from pydantic import Field

from app.shared.dto import APIModel


class KitchenOrderStatusRequest(APIModel):
    status: Literal["preparing", "ready_for_pickup"]
    note: str | None = Field(default=None, max_length=250)
