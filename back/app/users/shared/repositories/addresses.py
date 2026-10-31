"""MySQL address persistence adapter."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import Address


class SqlAlchemyAddressRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_owned(self, address_id: str, user_id: str, for_update: bool = False) -> Address | None:
        statement = select(Address).where(Address.id == address_id, Address.user_id == user_id)
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return self.session.scalar(statement)

    def list_for_user(self, user_id: str, for_update: bool = False) -> list[Address]:
        statement = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.asc(), Address.id.asc())
        )
        if for_update:
            statement = statement.with_for_update().execution_options(populate_existing=True)
        return list(self.session.scalars(statement))

    def add(self, address: Address) -> None:
        self.session.add(address)

    def delete(self, address: Address) -> None:
        self.session.delete(address)
