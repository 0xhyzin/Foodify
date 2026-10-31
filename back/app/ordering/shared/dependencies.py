"""Compose request-scoped adapters; the existing get_db dependency is shared."""

from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.ordering.infrastructure.cart_repository import SqlAlchemyCartRepository
from app.ordering.infrastructure.catalog_repository import SqlAlchemyCatalogRepository
from app.ordering.infrastructure.order_repository import SqlAlchemyOrderRepository
from app.ordering.infrastructure.payments import ConfiguredPaymentGateway
from app.ordering.shared.interfaces import (
    CartRepository,
    CatalogRepository,
    OrderRepository,
    PaymentGateway,
)
from app.users.shared.dependencies.resources import DB


def get_catalog_repository(db: DB) -> CatalogRepository:
    return SqlAlchemyCatalogRepository(db)


def get_cart_repository(db: DB) -> CartRepository:
    return SqlAlchemyCartRepository(db)


def get_order_repository(db: DB) -> OrderRepository:
    return SqlAlchemyOrderRepository(db)


def get_payment_gateway() -> PaymentGateway:
    settings = get_settings()
    return ConfiguredPaymentGateway(settings)


Catalog = Annotated[CatalogRepository, Depends(get_catalog_repository)]
Carts = Annotated[CartRepository, Depends(get_cart_repository)]
Orders = Annotated[OrderRepository, Depends(get_order_repository)]
Payments = Annotated[PaymentGateway, Depends(get_payment_gateway)]
