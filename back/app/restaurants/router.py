from fastapi import APIRouter

from app.restaurants.browse_categories.router import router as browse_categories_router
from app.restaurants.get_restaurant.router import router as get_restaurant_router
from app.restaurants.list_categories.router import router as list_categories_router
from app.restaurants.list_favorites.router import router as list_favorites_router
from app.restaurants.list_menu.router import router as list_menu_router
from app.restaurants.list_restaurants.router import router as list_restaurants_router
from app.restaurants.set_favorite.router import router as set_favorite_router

"""Assemble operation routers only."""
router = APIRouter()
router.include_router(list_restaurants_router)
router.include_router(get_restaurant_router)
router.include_router(list_categories_router)
router.include_router(list_menu_router)
router.include_router(browse_categories_router)
router.include_router(list_favorites_router)
router.include_router(set_favorite_router)
