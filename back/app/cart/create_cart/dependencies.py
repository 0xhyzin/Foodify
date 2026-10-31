"""Compose explicit cart creation using the existing request-scoped transaction."""

from typing import Annotated

from fastapi import Depends

from app.cart.create_cart.interfaces import CreateCartServiceInterface
from app.cart.create_cart.service import CreateCartService
from app.ordering.shared.dependencies import Carts, Catalog
from app.shared.ports import UnitOfWork
from app.users.shared.dependencies import get_unit_of_work, get_user_repository
from app.users.shared.interfaces import UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]
Transaction = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_service(
    users: Users, carts: Carts, catalog: Catalog, uow: Transaction
) -> CreateCartServiceInterface:
    return CreateCartService(users, carts, catalog, uow)
