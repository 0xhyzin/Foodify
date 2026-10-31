from app.ordering.shared.interfaces import OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData, GetOrderResponse
from app.payments.shared.dto import TransferClaim
from app.payments.shared.guards import lock_owned_order
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.users.shared.interfaces import UserRepository


class ClaimTransferService:
    def __init__(self, users: UserRepository, orders: OrderRepository, uow: UnitOfWork) -> None:
        self.users, self.orders, self.uow = users, orders, uow

    def execute(self, user_id: str, order_id: str, payload: TransferClaim) -> GetOrderResponse:
        order = lock_owned_order(self.users, self.orders, user_id, order_id)
        if (
            not order.payment
            or order.payment.provider != "manual_transfer"
            or order.payment.status not in {"awaiting_transfer", "pending_review", "rejected"}
        ):
            raise AppError(
                "transfer_not_allowed", "This order cannot receive a transfer claim.", 409
            )
        order.payment.claimed_reference = payload.reference.strip()
        order.payment.status = "pending_review"
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()
        return response
