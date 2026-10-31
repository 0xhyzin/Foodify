from app.ordering.models import OrderEvent
from app.ordering.shared.interfaces import CartRepository, OrderRepository
from app.ordering.shared.mappers import order_view
from app.orders.get_order.dto import GetOrderData, GetOrderResponse
from app.payments.shared.dto import TransferReview
from app.payments.shared.guards import lock_owned_order
from app.payments.shared.state import confirm_paid_order
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class ReviewTransferService:
    def __init__(
        self, users: UserRepository, orders: OrderRepository, carts: CartRepository, uow: UnitOfWork
    ) -> None:
        self.users, self.orders, self.carts, self.uow = users, orders, carts, uow

    def execute(self, actor_id: str, order_id: str, payload: TransferReview) -> GetOrderResponse:
        found = self.orders.get_locked(order_id)
        if found is None:
            raise AppError("order_not_found", "Order not found.", 404)
        # Release this read lock before acquiring the common parent lock in a stable order.
        owner_id = found.user_id
        self.uow.rollback()
        order = lock_owned_order(self.users, self.orders, owner_id, order_id, active_account=False)
        if (
            not order.payment
            or order.payment.provider != "manual_transfer"
            or order.payment.status != "pending_review"
        ):
            raise AppError(
                "transfer_not_pending", "Only pending transfer claims can be reviewed.", 409
            )
        if payload.decision == "approve":
            order.payment.verified_reference = payload.verified_reference.strip().lower()
            confirm_paid_order(order, self.carts, actor_id)
        else:
            order.payment.status = "rejected"
        order.events.append(
            OrderEvent(
                status=order.status,
                actor_id=actor_id,
                note=f"Transfer {payload.decision}: {payload.note}",
                created_at=utcnow(),
            )
        )
        self.uow.flush()  # Unique verified reference prevents reusing one bank transaction.
        response = GetOrderResponse(data=GetOrderData(order=order_view(order)))
        self.uow.commit()
        return response
