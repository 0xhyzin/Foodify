"""HTTP endpoint for adding an owned delivery address."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.addresses.add_address.dependencies import get_service
from app.users.addresses.add_address.dto import AddAddressRequest, AddAddressResponse
from app.users.addresses.add_address.interfaces import AddAddressServiceInterface

router = APIRouter(tags=["Customer profile"])
AddressOwner = Annotated[User, Depends(require_permission("addresses:manage"))]
AddressService = Annotated[AddAddressServiceInterface, Depends(get_service)]


@router.post(
    "/me/addresses", response_model=AddAddressResponse, status_code=status.HTTP_201_CREATED
)
def add_my_address(
    payload: AddAddressRequest,
    current_user: AddressOwner,
    service: AddressService,
) -> AddAddressResponse:
    """Add an address; the first address automatically becomes the default."""
    return service.execute(current_user.id, payload)
