"""Bounded catalog SQL queries; wildcard search is treated as literal text."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ordering.models import BrowseCategory, FavoriteRestaurant, MenuItem, Restaurant


def literal_search(value: str) -> str:
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")


class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_restaurants(
        self,
        category: str | None,
        search: str | None,
        limit: int,
        offset: int,
        kind: str | None = None,
        sort: str = "rating",
        free_delivery: bool = False,
        max_delivery_minutes: int | None = None,
    ) -> list[Restaurant]:
        stmt = select(Restaurant).where(Restaurant.is_active.is_(True))
        if category:
            code = category.strip().lower()
            stmt = stmt.where(
                or_(
                    func.lower(Restaurant.category) == code,
                    Restaurant.categories.any(BrowseCategory.code == code),
                )
            )
        if kind:
            stmt = stmt.where(Restaurant.kind == kind)
        if free_delivery:
            stmt = stmt.where(Restaurant.delivery_fee == 0)
        if max_delivery_minutes:
            stmt = stmt.where(Restaurant.delivery_minutes <= max_delivery_minutes)
        if search and search.strip():
            stmt = stmt.where(
                or_(
                    Restaurant.name.ilike(f"%{literal_search(search.strip())}%", escape="!"),
                    select(MenuItem.id)
                    .where(
                        MenuItem.restaurant_id == Restaurant.id,
                        MenuItem.is_available.is_(True),
                        MenuItem.name.ilike(f"%{literal_search(search.strip())}%", escape="!"),
                    )
                    .exists(),
                )
            )
        ordering = {
            "rating": Restaurant.rating.desc(),
            "fastest": Restaurant.delivery_minutes.asc(),
            "delivery_fee": Restaurant.delivery_fee.asc(),
        }[sort]
        return list(
            self.session.scalars(
                stmt.order_by(ordering, Restaurant.name, Restaurant.id).limit(limit).offset(offset)
            )
        )

    def list_browse_categories(self) -> list[BrowseCategory]:
        return list(
            self.session.scalars(select(BrowseCategory).order_by(BrowseCategory.code).limit(100))
        )

    def list_favorites(self, user_id: str, for_update: bool = False) -> list[str]:
        statement = (
            select(FavoriteRestaurant.restaurant_id)
            .where(FavoriteRestaurant.user_id == user_id)
            .order_by(FavoriteRestaurant.restaurant_id)
            .limit(200)
        )
        if for_update:
            statement = statement.with_for_update()
        return list(self.session.scalars(statement))

    def set_favorite(self, user_id: str, restaurant_id: str, favorite: bool) -> None:
        existing = self.session.scalar(
            select(FavoriteRestaurant)
            .where(
                FavoriteRestaurant.user_id == user_id,
                FavoriteRestaurant.restaurant_id == restaurant_id,
            )
            .with_for_update()
        )
        if favorite and existing is None:
            self.session.add(FavoriteRestaurant(user_id=user_id, restaurant_id=restaurant_id))
        elif not favorite and existing is not None:
            self.session.delete(existing)

    def get_restaurant(self, restaurant_id: str, for_update: bool = False) -> Restaurant | None:
        stmt = select(Restaurant).where(Restaurant.id == restaurant_id)
        if for_update:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(stmt)

    def list_categories(self, restaurant_id: str) -> list[str]:
        return list(
            self.session.scalars(
                select(MenuItem.category)
                .where(MenuItem.restaurant_id == restaurant_id, MenuItem.is_available.is_(True))
                .distinct()
                .order_by(MenuItem.category)
                .limit(100)
            )
        )

    def list_menu(
        self, restaurant_id: str, category: str | None, limit: int, offset: int
    ) -> list[MenuItem]:
        stmt = select(MenuItem).where(
            MenuItem.restaurant_id == restaurant_id, MenuItem.is_available.is_(True)
        )
        if category:
            stmt = stmt.where(func.lower(MenuItem.category) == category.strip().lower())
        return list(
            self.session.scalars(
                stmt.order_by(MenuItem.name, MenuItem.id).limit(limit).offset(offset)
            )
        )

    def get_menu_item(self, item_id: str, for_update: bool = False) -> MenuItem | None:
        stmt = select(MenuItem).where(MenuItem.id == item_id)
        if for_update:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(stmt)

    def get_menu_items(self, item_ids: list[str], for_update: bool = False) -> list[MenuItem]:
        if not item_ids:
            return []
        statement = select(MenuItem).where(MenuItem.id.in_(item_ids)).order_by(MenuItem.id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return list(self.session.scalars(statement))
