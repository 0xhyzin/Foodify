"""View mapping is separate from HTTP handlers and persistence queries."""

from datetime import UTC
from decimal import Decimal

from app.ordering.models import Cart, FoodOrder, MenuItem, Restaurant
from app.ordering.shared.dto import (
    CartData,
    CartLineView,
    CartResponse,
    CartView,
    MenuItemView,
    OrderLineView,
    OrderView,
    PaymentView,
    RestaurantView,
)
from app.ordering.shared.pricing import ZERO, money


def restaurant_view(value: Restaurant) -> RestaurantView:
    return RestaurantView(
        id=value.id,
        name=value.name,
        category=value.category,
        rating=value.rating,
        reviews=value.reviews,
        time=value.delivery_minutes,
        address=value.address,
        image=value.image,
        description=value.description,
        delivery_fee=value.delivery_fee,
        kind=value.kind,
        slug=value.slug,
        logo=value.logo,
        artwork=value.artwork,
        tags=[category.code for category in value.categories],
    )


def menu_view(value: MenuItem) -> MenuItemView:
    return MenuItemView(
        id=value.id,
        restaurant_id=value.restaurant_id,
        name=value.name,
        category=value.category,
        price=value.price,
        desc=value.description,
        image=value.image,
        available=value.is_available,
        artwork=value.artwork,
    )


def cart_response(
    cart: Cart | None, delivery_fee: Decimal = ZERO, restaurant_active: bool = True
) -> CartResponse:
    lines = []
    if cart is not None:
        for entry in cart.items:
            menu = entry.menu_item
            lines.append(
                CartLineView(
                    id=entry.id,
                    menu_item_id=menu.id,
                    name=menu.name,
                    price=menu.price,
                    quantity=entry.quantity,
                    line_total=money(menu.price * entry.quantity),
                    image=menu.image,
                    available=menu.is_available and restaurant_active,
                )
            )
    subtotal = money(sum((line.line_total for line in lines), ZERO))
    fee = money(delivery_fee) if lines else ZERO
    return CartResponse(
        data=CartData(
            cart=CartView(
                id=cart.id if cart else None,
                restaurant_id=cart.restaurant_id if cart else None,
                revision=cart.revision if cart else 0,
                items=lines,
                subtotal=subtotal,
                delivery_fee=fee,
                total=money(subtotal + fee),
            )
        )
    )


def order_view(order: FoodOrder) -> OrderView:
    payment = order.payment
    payment_view = (
        None
        if payment is None
        else PaymentView(
            provider=payment.provider,
            status=payment.status,
            amount=payment.amount,
            reference=payment.reference,
            is_simulated=payment.provider in {"simulation", "sandbox"} or bool(payment.test_mode),
            claimed_reference=payment.claimed_reference,
            transfer_recipient=payment.transfer_recipient,
            transfer_recipient_name=payment.transfer_recipient_name,
        )
    )
    return OrderView(
        id=order.id,
        restaurant_id=order.restaurant_id,
        address_id=order.address_id,
        delivery_address=order.delivery_address,
        status=order.status,
        payment_method=order.payment_method,
        payment_status=payment.status if payment else "unknown",
        payment=payment_view,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        currency=order.currency,
        created_at=order.created_at.replace(tzinfo=UTC),
        events=[
            {
                "status": event.status,
                "note": event.note,
                "created_at": event.created_at.replace(tzinfo=UTC),
            }
            for event in order.events
        ],
        items=[
            OrderLineView(
                menu_item_id=line.menu_item_id,
                name=line.item_name,
                unit_price=line.unit_price,
                quantity=line.quantity,
                line_total=money(line.unit_price * line.quantity),
            )
            for line in order.items
        ],
    )
