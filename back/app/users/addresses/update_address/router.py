"""HTTP endpoint for replacing an owned delivery address."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.addresses.update_address.dependencies import get_service
from app.users.addresses.update_address.dto import UpdateAddressRequest, UpdateAddressResponse
from app.users.addresses.update_address.interfaces import UpdateAddressServiceInterface

router = APIRouter(tags=["Customer profile"])
AddressOwner = Annotated[User, Depends(require_permission("addresses:manage"))]
AddressService = Annotated[UpdateAddressServiceInterface, Depends(get_service)]


@router.put("/me/addresses/{address_id}", response_model=UpdateAddressResponse)
def replace_my_address(
    address_id: UUID,
    payload: UpdateAddressRequest,
    current_user: AddressOwner,
    service: AddressService,
) -> UpdateAddressResponse:
    """Replace all address fields; an address must belong to the caller."""
    return service.execute(current_user.id, str(address_id), payload)
