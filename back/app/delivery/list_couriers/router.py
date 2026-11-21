"""Active courier directory endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.ordering.shared.dependencies import Staff
from app.shared.dto import APIModel

router = APIRouter(tags=["Delivery"])


class CourierView(APIModel):
    id: str
    name: str
    phone: str | None
    active_order_count: int


class CourierListData(APIModel):
    couriers: list[CourierView]


class CourierListResponse(APIModel):
    data: CourierListData


@router.get("/delivery/couriers", response_model=CourierListResponse)
def list_couriers(
    _actor: Annotated[User, Depends(require_permission("deliveries:assign"))],
    staff: Staff,
) -> CourierListResponse:
    entries = staff.list_active_couriers()
    return CourierListResponse(
        data=CourierListData(
            couriers=[
                CourierView(
                    id=user.id,
                    name=user.name,
                    phone=user.phone,
                    active_order_count=count,
                )
                for user, count in entries
            ]
        )
    )
