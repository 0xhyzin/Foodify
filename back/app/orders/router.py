from fastapi import APIRouter

from app.orders.get_order.router import router as get_order_router
from app.orders.list_orders.router import router as list_orders_router
from app.orders.list_restaurant_orders.router import router as list_restaurant_orders_router
from app.orders.update_status.router import router as update_status_router

"""Assemble operation routers only."""
router = APIRouter()
router.include_router(list_orders_router)
router.include_router(get_order_router)
router.include_router(list_restaurant_orders_router)
router.include_router(update_status_router)
