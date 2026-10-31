"""Inject repository interfaces and a shared request transaction."""

from typing import Annotated

from fastapi import Depends

from app.cart.add_item.interfaces import AddCartItemServiceInterface
from app.cart.add_item.service import AddCartItemService
from app.ordering.shared.dependencies import Carts, Catalog
from app.shared.ports import UnitOfWork
from app.users.shared.dependencies import get_unit_of_work, get_user_repository
from app.users.shared.interfaces import UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]
Transaction = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_service(
    users: Users, carts: Carts, catalog: Catalog, uow: Transaction
) -> AddCartItemServiceInterface:
    return AddCartItemService(users, carts, catalog, uow)
