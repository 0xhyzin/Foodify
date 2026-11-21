"""DTO contracts for assigning preparers and listing preparer directory."""

from uuid import UUID

from app.shared.dto import APIModel


class AssignPreparerRequest(APIModel):
    preparer_id: UUID


class PreparerView(APIModel):
    id: str
    name: str
    phone: str | None
    active_order_count: int


class PreparerListData(APIModel):
    preparers: list[PreparerView]


class PreparerListResponse(APIModel):
    data: PreparerListData
