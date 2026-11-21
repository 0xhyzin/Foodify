"""Restaurant staff scoping and courier directory SQL queries."""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.infrastructure.models import Role, User
from app.ordering.models import DeliveryAssignment, FoodOrder, Restaurant, RestaurantStaff
from app.shared.time import utcnow

TERMINAL_ORDER_STATUSES = ("delivered", "rejected", "cancelled")


class SqlAlchemyRestaurantStaffRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def is_assigned(self, restaurant_id: str, user_id: str) -> bool:
        return (
            self.session.scalar(
                select(RestaurantStaff.user_id).where(
                    RestaurantStaff.restaurant_id == restaurant_id,
                    RestaurantStaff.user_id == user_id,
                )
            )
            is not None
        )

    def list_managed_restaurants(self, user_id: str) -> list[Restaurant]:
        return list(
            self.session.scalars(
                select(Restaurant)
                .join(RestaurantStaff, RestaurantStaff.restaurant_id == Restaurant.id)
                .where(RestaurantStaff.user_id == user_id, Restaurant.is_active.is_(True))
                .order_by(Restaurant.name, Restaurant.id)
            )
        )

    def list_all_active_restaurants(self) -> list[Restaurant]:
        return list(
            self.session.scalars(
                select(Restaurant)
                .where(Restaurant.is_active.is_(True))
                .order_by(Restaurant.name, Restaurant.id)
            )
        )

    def list_active_couriers(self) -> list[tuple[User, int]]:
        active_count = func.count(FoodOrder.id)
        rows = self.session.execute(
            select(User, active_count)
            .join(User.roles)
            .outerjoin(
                DeliveryAssignment, DeliveryAssignment.delivery_person_id == User.id
            )
            .outerjoin(
                FoodOrder,
                and_(
                    FoodOrder.id == DeliveryAssignment.order_id,
                    FoodOrder.status.notin_(TERMINAL_ORDER_STATUSES),
                ),
            )
            .where(User.is_active.is_(True), Role.code == "courier")
            .group_by(User.id)
            .order_by(User.name, User.id)
        ).all()
        return [(user, int(count)) for user, count in rows]

    def list_active_preparers(
        self, restaurant_id: str | None = None
    ) -> list[tuple[User, int]]:
        active_count = func.count(FoodOrder.id)
        stmt = (
            select(User, active_count)
            .join(User.roles)
            .outerjoin(
                FoodOrder,
                and_(
                    FoodOrder.assigned_preparer_id == User.id,
                    FoodOrder.status.in_(("accepted", "preparing")),
                ),
            )
            .where(User.is_active.is_(True), Role.code == "order_preparer")
        )
        if restaurant_id:
            stmt = stmt.join(
                RestaurantStaff,
                and_(
                    RestaurantStaff.user_id == User.id,
                    RestaurantStaff.restaurant_id == restaurant_id,
                ),
            )
        rows = self.session.execute(stmt.group_by(User.id).order_by(User.name, User.id)).all()
        return [(user, int(count)) for user, count in rows]

    def list_preparer_user_ids_for_restaurant(self, restaurant_id: str) -> list[str]:
        return list(
            self.session.scalars(
                select(User.id)
                .join(User.roles)
                .join(RestaurantStaff, RestaurantStaff.user_id == User.id)
                .where(
                    User.is_active.is_(True),
                    Role.code == "order_preparer",
                    RestaurantStaff.restaurant_id == restaurant_id,
                )
                .order_by(User.id)
            )
        )

    def assign_staff(self, restaurant_id: str, user_id: str) -> None:
        if not self.is_assigned(restaurant_id, user_id):
            self.session.add(
                RestaurantStaff(restaurant_id=restaurant_id, user_id=user_id, created_at=utcnow())
            )
