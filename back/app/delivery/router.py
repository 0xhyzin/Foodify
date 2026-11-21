"""Assemble delivery routers only."""

from fastapi import APIRouter

from app.delivery.assign_order.router import router as assign_order_router
from app.delivery.list_couriers.router import router as list_couriers_router
from app.delivery.my_orders.router import router as my_orders_router
from app.delivery.reassign_order.router import router as reassign_order_router
from app.delivery.update_status.router import router as update_status_router

router = APIRouter()
router.include_router(assign_order_router)
router.include_router(reassign_order_router)
router.include_router(list_couriers_router)
router.include_router(my_orders_router)
router.include_router(update_status_router)
