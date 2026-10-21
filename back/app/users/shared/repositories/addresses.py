"""MySQL address persistence adapter."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.models import Address


class SqlAlchemyAddressRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_owned(self, address_id: str, user_id: str) -> Address | None:
        return self.session.scalar(
            select(Address).where(Address.id == address_id, Address.user_id == user_id)
        )

    def list_for_user(self, user_id: str) -> list[Address]:
        return list(
            self.session.scalars(
                select(Address)
                .where(Address.user_id == user_id)
                .order_by(Address.created_at.asc(), Address.id.asc())
            )
        )

    def add(self, address: Address) -> None:
        self.session.add(address)

    def delete(self, address: Address) -> None:
        self.session.delete(address)
