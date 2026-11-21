"""Endpoints for listing preparers and assigning an order preparer."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.ordering.shared.dependencies import Staff
from app.ordering.shared.guards import assert_can_manage_restaurant, is_global_operator
from app.orders.get_order.dto import GetOrderResponse

from .dependencies import get_service
from .dto import AssignPreparerRequest, PreparerListData, PreparerListResponse, PreparerView
from .interfaces import AssignPreparerServiceInterface

router = APIRouter(tags=["Operations orders"])
Manager = Annotated[User, Depends(require_permission("orders:manage"))]


@router.get("/operations/preparers", response_model=PreparerListResponse)
def list_preparers(
    actor: Manager,
    staff: Staff,
    restaurant_id: UUID | None = None,
) -> PreparerListResponse:
    scoped_restaurant: str | None = str(restaurant_id) if restaurant_id else None
    if scoped_restaurant:
        assert_can_manage_restaurant(actor, scoped_restaurant, staff)
    elif not is_global_operator(actor):
        managed = staff.list_managed_restaurants(actor.id)
        if not managed:
            return PreparerListResponse(data=PreparerListData(preparers=[]))
        scoped_restaurant = managed[0].id
    entries = staff.list_active_preparers(scoped_restaurant)
    return PreparerListResponse(
        data=PreparerListData(
            preparers=[
                PreparerView(
                    id=user.id,
                    name=user.name,
                    phone=user.phone,
                    active_order_count=count,
                )
                for user, count in entries
            ]
        )
    )


@router.post("/orders/{order_id}/preparer-assignment", response_model=GetOrderResponse)
@router.patch("/orders/{order_id}/preparer-assignment", response_model=GetOrderResponse)
def assign_preparer(
    order_id: UUID,
    payload: AssignPreparerRequest,
    actor: Manager,
    service: Annotated[AssignPreparerServiceInterface, Depends(get_service)],
) -> GetOrderResponse:
    return service.execute(actor, str(order_id), payload)
