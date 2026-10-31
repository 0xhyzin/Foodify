"""Serialize checkout, preserve delivery history, and atomically persist the result."""

from hashlib import sha256

from app.checkout.submit_order.dto import CheckoutData, CheckoutRequest, CheckoutResponse
from app.ordering.models import FoodOrder, FoodOrderItem, OrderEvent, Payment
from app.ordering.shared.cart_state import load_cart_menu, lock_cart
from app.ordering.shared.guards import require_restaurant
from app.ordering.shared.interfaces import (
    CartRepository,
    CatalogRepository,
    OrderRepository,
    PaymentGateway,
)
from app.ordering.shared.mappers import order_view
from app.ordering.shared.pricing import MAX_TOTAL, ZERO, money
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.dto.address import AddressWriteRequest
from app.users.shared.interfaces import AddressRepository, UserRepository


class CheckoutService:
    def __init__(
        self,
        users: UserRepository,
        addresses: AddressRepository,
        carts: CartRepository,
        catalog: CatalogRepository,
        orders: OrderRepository,
        payments: PaymentGateway,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.addresses, self.carts = users, addresses, carts
        self.catalog, self.orders, self.payments, self.uow = catalog, orders, payments, uow

    def execute(self, user_id: str, key: str, payload: CheckoutRequest) -> CheckoutResponse:
        cart = lock_cart(self.users, self.carts, self.uow, user_id, str(payload.restaurant_id))
        fingerprint = sha256(
            f"{payload.restaurant_id}:{payload.address_id}:{payload.payment_method}:{money(payload.expected_total)}:{payload.cart_revision}".encode()
        ).hexdigest()
        previous = self.orders.get_by_checkout_key(user_id, key)
        if previous is not None:
            if previous.checkout_fingerprint != fingerprint:
                raise AppError(
                    "idempotency_key_reused",
                    "Use a new Idempotency-Key for a different checkout request.",
                    409,
                )
            return CheckoutResponse(
                data=CheckoutData(
                    order=order_view(previous),
                    confirmation="This checkout was already completed.",
                    is_replay=True,
                )
            )
        if not cart.items:
            raise AppError("empty_cart", "Add items before checkout.", 400)
        if cart.revision != payload.cart_revision:
            raise AppError(
                "cart_changed", "Your cart changed. Review it before submitting again.", 409
            )
        restaurant = require_restaurant(self.catalog, cart.restaurant_id, for_update=True)
        # Current, locked menu rows are required; login may have opened an older RR snapshot.
        load_cart_menu(self.catalog, cart, for_update=True)
        if any(not entry.menu_item.is_available for entry in cart.items):
            raise AppError("menu_item_unavailable", "One or more items are unavailable.", 409)
        address = self.addresses.get_owned(str(payload.address_id), user_id, for_update=True)
        if address is None:
            raise AppError("address_not_found", "Select one of your saved delivery addresses.", 404)
        delivery_address = AddressWriteRequest.model_validate(address).model_dump(mode="json")
        subtotal = money(sum((line.menu_item.price * line.quantity for line in cart.items), ZERO))
        fee = money(restaurant.delivery_fee)
        total = money(subtotal + fee)
        if total != money(payload.expected_total):
            raise AppError(
                "cart_price_changed", "Prices changed. Review the updated cart before paying.", 409
            )
        if total > MAX_TOTAL:
            raise AppError("order_total_limit", "Order total exceeds the supported limit.", 409)
        # Preparing state never claims a real external charge succeeded.
        result = self.payments.authorize(total, payload.payment_method)
        submitted = result.status in {"simulated", "due_on_delivery"}
        order_status = "placed" if submitted else "awaiting_payment"
        order = FoodOrder(
            user_id=user_id,
            restaurant_id=restaurant.id,
            address_id=address.id,
            delivery_address=delivery_address,
            checkout_key=key,
            checkout_fingerprint=fingerprint,
            status=order_status,
            cart_id=cart.id,
            cart_revision=cart.revision,
            payment_method=payload.payment_method,
            subtotal=subtotal,
            delivery_fee=fee,
            total=total,
            currency="EGP",
            created_at=utcnow(),
            items=[
                FoodOrderItem(
                    menu_item_id=line.menu_item_id,
                    item_name=line.menu_item.name,
                    unit_price=line.menu_item.price,
                    quantity=line.quantity,
                )
                for line in cart.items
            ],
            payment=Payment(
                provider=result.provider,
                status=result.status,
                amount=total,
                reference=result.reference,
                test_mode=result.test_mode,
                transfer_recipient=result.recipient,
                transfer_recipient_name=result.recipient_name,
            ),
            events=[OrderEvent(status=order_status, actor_id=user_id, created_at=utcnow())],
        )
        self.orders.add(order)
        # Online/manual payments keep this cart until verified payment. Other carts are untouched.
        if submitted:
            cart.items.clear()
            cart.revision += 1
            cart.updated_at = utcnow()
        self.uow.flush()
        # Construct and validate the complete public DTO before the transaction commits.
        response = CheckoutResponse(
            data=CheckoutData(
                order=order_view(order),
                confirmation="Order submitted."
                if submitted
                else "Order saved. Complete payment to confirm it.",
                is_replay=False,
            )
        )
        self.uow.commit()
        return response
