"""Checkout composes separate account, catalog, cart, order, and payment ports."""

from typing import Annotated

from fastapi import Depends

from app.checkout.submit_order.interfaces import CheckoutServiceInterface
from app.checkout.submit_order.service import CheckoutService
from app.ordering.shared.dependencies import Carts, Catalog, Orders, Payments
from app.shared.ports import UnitOfWork
from app.users.shared.dependencies import (
    get_address_repository,
    get_unit_of_work,
    get_user_repository,
)
from app.users.shared.interfaces import AddressRepository, UserRepository

Users = Annotated[UserRepository, Depends(get_user_repository)]
Addresses = Annotated[AddressRepository, Depends(get_address_repository)]
Transaction = Annotated[UnitOfWork, Depends(get_unit_of_work)]


def get_service(
    users: Users,
    addresses: Addresses,
    carts: Carts,
    catalog: Catalog,
    orders: Orders,
    payments: Payments,
    uow: Transaction,
) -> CheckoutServiceInterface:
    return CheckoutService(users, addresses, carts, catalog, orders, payments, uow)
