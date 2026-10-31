"""Payment settlement updates one immutable order and only its unchanged merchant cart."""

from app.ordering.models import FoodOrder, OrderEvent
from app.ordering.shared.interfaces import CartRepository
from app.shared.time import utcnow


def confirm_paid_order(
    order: FoodOrder, carts: CartRepository, actor_id: str | None = None
) -> None:
    order.payment.status = "paid"
    if order.status == "awaiting_payment":
        order.status = "placed"
        order.events.append(
            OrderEvent(
                status="placed", actor_id=actor_id, created_at=utcnow(), note="Payment verified."
            )
        )
    cart = carts.get_for_user(order.user_id, order.restaurant_id, for_update=True)
    # New items or quantity edits made while paying are never silently discarded.
    if cart and cart.id == order.cart_id and cart.revision == order.cart_revision:
        cart.items.clear()
        cart.revision += 1
        cart.updated_at = utcnow()
