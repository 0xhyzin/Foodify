from fastapi import APIRouter

from app.orders.assign_preparer.router import router as assign_preparer_router
from app.orders.cancel_order.router import router as cancel_order_router
from app.orders.get_order.router import router as get_order_router
from app.orders.kitchen.router import router as kitchen_router
from app.orders.list_managed_restaurants.router import router as list_managed_restaurants_router
from app.orders.list_orders.router import router as list_orders_router
from app.orders.list_restaurant_orders.router import router as list_restaurant_orders_router
from app.orders.update_status.router import router as update_status_router

"""Assemble operation routers only."""
router = APIRouter()
router.include_router(list_orders_router)
router.include_router(get_order_router)
router.include_router(cancel_order_router)
router.include_router(list_managed_restaurants_router)
router.include_router(list_restaurant_orders_router)
router.include_router(update_status_router)
router.include_router(assign_preparer_router)
router.include_router(kitchen_router)
