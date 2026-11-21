"""Manager services for creating/updating restaurants, menu items, and staff links."""

from app.infrastructure.models import User
from app.ordering.models import MenuItem, Restaurant
from app.ordering.shared.guards import assert_can_manage_restaurant, is_global_operator
from app.ordering.shared.interfaces import CatalogRepository, RestaurantStaffRepository
from app.ordering.shared.mappers import menu_view, restaurant_view
from app.ordering.shared.pricing import money
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository

from .dto import (
    AssignRestaurantStaffRequest,
    AssignStaffData,
    AssignStaffResponse,
    CreateMenuItemRequest,
    CreateRestaurantRequest,
    ManageMenuItemResponse,
    ManageRestaurantResponse,
    MenuItemData,
    RestaurantData,
    UpdateMenuItemRequest,
    UpdateRestaurantRequest,
)

STAFF_LINKABLE_ROLES = frozenset({"restaurant_manager", "order_preparer"})


class ManageRestaurantsService:
    def __init__(
        self,
        catalog: CatalogRepository,
        staff: RestaurantStaffRepository,
        users: UserRepository,
        uow: UnitOfWork,
    ) -> None:
        self.catalog, self.staff, self.users, self.uow = catalog, staff, users, uow

    def create_restaurant(
        self, actor: User, payload: CreateRestaurantRequest
    ) -> ManageRestaurantResponse:
        if not is_global_operator(actor):
            raise AppError(
                "permission_denied",
                "Only operations managers or administrators can add new restaurants.",
                403,
            )
        restaurant = Restaurant(
            name=payload.name.strip(),
            category=payload.category.strip(),
            kind=payload.kind,
            address=payload.address.strip(),
            delivery_fee=money(payload.delivery_fee),
            delivery_minutes=payload.delivery_minutes,
            description=payload.description.strip() if payload.description else None,
            artwork=payload.artwork.strip() or "burger",
            image=payload.image.strip() if payload.image else None,
            is_active=payload.is_active,
            created_at=utcnow(),
            categories=[],
        )
        self.catalog.add_restaurant(restaurant)
        self.uow.flush()
        response = ManageRestaurantResponse(
            data=RestaurantData(restaurant=restaurant_view(restaurant))
        )
        self.uow.commit()
        return response

    def update_restaurant(
        self, actor: User, restaurant_id: str, payload: UpdateRestaurantRequest
    ) -> ManageRestaurantResponse:
        assert_can_manage_restaurant(actor, restaurant_id, self.staff)
        restaurant = self.catalog.get_restaurant(restaurant_id, for_update=True)
        if restaurant is None:
            raise AppError("restaurant_not_found", "Restaurant not found.", 404)
        fields = payload.model_fields_set
        if "name" in fields and payload.name is not None:
            restaurant.name = payload.name.strip()
        if "category" in fields and payload.category is not None:
            restaurant.category = payload.category.strip()
        if "kind" in fields and payload.kind is not None:
            restaurant.kind = payload.kind
        if "address" in fields and payload.address is not None:
            restaurant.address = payload.address.strip()
        if "delivery_fee" in fields and payload.delivery_fee is not None:
            restaurant.delivery_fee = money(payload.delivery_fee)
        if "delivery_minutes" in fields and payload.delivery_minutes is not None:
            restaurant.delivery_minutes = payload.delivery_minutes
        if "description" in fields:
            restaurant.description = (
                payload.description.strip() if payload.description else None
            )
        if "artwork" in fields and payload.artwork is not None:
            restaurant.artwork = payload.artwork.strip() or "burger"
        if "image" in fields:
            restaurant.image = payload.image.strip() if payload.image else None
        if "is_active" in fields and payload.is_active is not None:
            restaurant.is_active = payload.is_active
        self.uow.flush()
        response = ManageRestaurantResponse(
            data=RestaurantData(restaurant=restaurant_view(restaurant))
        )
        self.uow.commit()
        return response

    def create_menu_item(
        self, actor: User, restaurant_id: str, payload: CreateMenuItemRequest
    ) -> ManageMenuItemResponse:
        assert_can_manage_restaurant(actor, restaurant_id, self.staff)
        restaurant = self.catalog.get_restaurant(restaurant_id, for_update=True)
        if restaurant is None:
            raise AppError("restaurant_not_found", "Restaurant not found.", 404)
        item = MenuItem(
            restaurant_id=restaurant.id,
            name=payload.name.strip(),
            category=payload.category.strip(),
            price=money(payload.price),
            description=payload.description.strip() if payload.description else None,
            artwork=payload.artwork.strip() or "burger",
            image=payload.image.strip() if payload.image else None,
            is_available=payload.is_available,
        )
        self.catalog.add_menu_item(item)
        self.uow.flush()
        response = ManageMenuItemResponse(data=MenuItemData(item=menu_view(item)))
        self.uow.commit()
        return response

    def update_menu_item(
        self, actor: User, restaurant_id: str, item_id: str, payload: UpdateMenuItemRequest
    ) -> ManageMenuItemResponse:
        assert_can_manage_restaurant(actor, restaurant_id, self.staff)
        item = self.catalog.get_menu_item(item_id, for_update=True)
        if item is None or item.restaurant_id != restaurant_id:
            raise AppError("menu_item_not_found", "Menu item not found.", 404)
        fields = payload.model_fields_set
        if "name" in fields and payload.name is not None:
            item.name = payload.name.strip()
        if "category" in fields and payload.category is not None:
            item.category = payload.category.strip()
        if "price" in fields and payload.price is not None:
            item.price = money(payload.price)
        if "description" in fields:
            item.description = payload.description.strip() if payload.description else None
        if "artwork" in fields and payload.artwork is not None:
            item.artwork = payload.artwork.strip() or "burger"
        if "image" in fields:
            item.image = payload.image.strip() if payload.image else None
        if "is_available" in fields and payload.is_available is not None:
            item.is_available = payload.is_available
        self.uow.flush()
        response = ManageMenuItemResponse(data=MenuItemData(item=menu_view(item)))
        self.uow.commit()
        return response

    def assign_staff(
        self, actor: User, restaurant_id: str, payload: AssignRestaurantStaffRequest
    ) -> AssignStaffResponse:
        if not is_global_operator(actor):
            raise AppError(
                "permission_denied",
                "Only operations managers or administrators can assign restaurant staff.",
                403,
            )
        restaurant = self.catalog.get_restaurant(restaurant_id)
        if restaurant is None:
            raise AppError("restaurant_not_found", "Restaurant not found.", 404)
        target = self.users.get_by_id(str(payload.user_id))
        if target is None:
            raise AppError("staff_user_not_found", "Staff user not found.", 404)
        if not target.is_active or not any(
            role.code in STAFF_LINKABLE_ROLES for role in target.roles
        ):
            raise AppError(
                "invalid_staff_role",
                "User must be an active restaurant manager or order preparer.",
                400,
            )
        self.staff.assign_staff(restaurant.id, target.id)
        self.uow.flush()
        self.uow.commit()
        return AssignStaffResponse(
            data=AssignStaffData(restaurant_id=restaurant.id, user_id=target.id)
        )
