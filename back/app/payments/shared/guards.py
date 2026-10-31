from app.ordering.models import FoodOrder
from app.ordering.shared.interfaces import OrderRepository
from app.shared.errors import AppError
from app.users.shared.guards import require_active_user
from app.users.shared.interfaces import UserRepository


def lock_owned_order(
    users: UserRepository,
    orders: OrderRepository,
    user_id: str,
    order_id: str,
    active_account: bool = True,
) -> FoodOrder:
    if active_account:
        require_active_user(users, user_id, for_update=True)
    elif users.get_by_id(user_id, for_update=True) is None:
        raise AppError("user_not_found", "User not found.", 404)
    order = orders.get_locked(order_id)
    if order is None or order.user_id != user_id:
        raise AppError("order_not_found", "Order not found.", 404)
    return order
