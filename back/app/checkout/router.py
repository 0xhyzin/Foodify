"""Assemble operation routers only."""

from fastapi import APIRouter

from app.checkout.submit_order.router import router as submit_order_router

router = APIRouter()
router.include_router(submit_order_router)
