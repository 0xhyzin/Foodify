"""Cart persistence; write reads use current row locks, not stale MVCC snapshots."""

from sqlalchemy import select
from sqlalchemy.orm import Session, attributes

from app.ordering.models import Cart, CartItem


class SqlAlchemyCartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_for_user(
        self, user_id: str, restaurant_id: str, for_update: bool = False
    ) -> Cart | None:
        stmt = select(Cart).where(Cart.user_id == user_id, Cart.restaurant_id == restaurant_id)
        if for_update:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        cart = self.session.scalar(stmt)
        if cart is not None:
            items = select(CartItem).where(CartItem.cart_id == cart.id).order_by(CartItem.id)
            if for_update:
                items = items.with_for_update().execution_options(populate_existing=True)
            attributes.set_committed_value(cart, "items", list(self.session.scalars(items)))
        return cart

    def list_for_user(self, user_id: str, limit: int = 100, offset: int = 0) -> list[Cart]:
        from sqlalchemy.orm import selectinload

        return list(
            self.session.scalars(
                select(Cart)
                .options(selectinload(Cart.items).selectinload(CartItem.menu_item))
                .where(Cart.user_id == user_id, Cart.restaurant_id.is_not(None), Cart.items.any())
                .order_by(Cart.updated_at.desc(), Cart.id)
                .limit(limit)
                .offset(offset)
            )
        )

    def add(self, cart: Cart) -> None:
        self.session.add(cart)
