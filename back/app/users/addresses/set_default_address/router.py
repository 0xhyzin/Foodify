"""HTTP endpoint for selecting the customer's default delivery address."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.addresses.set_default_address.dependencies import get_service
from app.users.addresses.set_default_address.dto import SetDefaultAddressResponse
from app.users.addresses.set_default_address.interfaces import SetDefaultAddressServiceInterface

router = APIRouter(tags=["Customer profile"])
AddressOwner = Annotated[User, Depends(require_permission("addresses:manage"))]
AddressService = Annotated[SetDefaultAddressServiceInterface, Depends(get_service)]


@router.put("/me/default-address/{address_id}", response_model=SetDefaultAddressResponse)
def set_my_default_address(
    address_id: UUID,
    current_user: AddressOwner,
    service: AddressService,
) -> SetDefaultAddressResponse:
    """Choose a default delivery address belonging to the caller."""
    return service.execute(current_user.id, str(address_id))
