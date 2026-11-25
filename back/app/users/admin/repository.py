"""SQLAlchemy query adapter for admin user listing and role resolution."""

from collections import defaultdict

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.infrastructure.models import Role, User
from app.ordering.models import RestaurantStaff


class SqlAlchemyAdminDirectoryRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_users(
        self, role_code: str | None, search: str | None, limit: int, offset: int
    ) -> list[User]:
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .order_by(User.created_at.desc())
        )
        if role_code:
            statement = statement.where(User.roles.any(Role.code == role_code))
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(User.name.ilike(pattern), User.email.ilike(pattern))
            )
        return list(self.session.scalars(statement.limit(limit).offset(offset)))

    def get_roles_by_codes(self, codes: list[str]) -> list[Role]:
        if not codes:
            return []
        unique_codes = list(dict.fromkeys(codes))
        roles = list(self.session.scalars(select(Role).where(Role.code.in_(unique_codes))))
        by_code = {role.code: role for role in roles}
        return [by_code[code] for code in unique_codes if code in by_code]

    def list_managed_restaurant_map(self, user_ids: list[str]) -> dict[str, list[str]]:
        if not user_ids:
            return {}
        rows = self.session.execute(
            select(RestaurantStaff.user_id, RestaurantStaff.restaurant_id).where(
                RestaurantStaff.user_id.in_(user_ids)
            )
        ).all()
        mapping: dict[str, list[str]] = defaultdict(list)
        for user_id, restaurant_id in rows:
            mapping[user_id].append(restaurant_id)
        return dict(mapping)
