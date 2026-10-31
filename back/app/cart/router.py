from fastapi import APIRouter

from app.cart.add_item.router import router as add_item_router
from app.cart.clear_cart.router import router as clear_cart_router
from app.cart.create_cart.router import router as create_cart_router
from app.cart.get_cart.router import router as get_cart_router
from app.cart.list_carts.router import router as list_carts_router
from app.cart.remove_item.router import router as remove_item_router
from app.cart.update_item.router import router as update_item_router

"""Assemble operation routers only."""
router = APIRouter()
router.include_router(get_cart_router)
router.include_router(create_cart_router)
router.include_router(add_item_router)
router.include_router(update_item_router)
router.include_router(remove_item_router)
router.include_router(clear_cart_router)
router.include_router(list_carts_router)
