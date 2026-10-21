"""HTTP endpoint for listing owned delivery addresses."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.addresses.list_addresses.dependencies import get_service
from app.users.addresses.list_addresses.dto import ListAddressesResponse
from app.users.addresses.list_addresses.interfaces import ListAddressesServiceInterface

router = APIRouter(tags=["Customer profile"])
AddressOwner = Annotated[User, Depends(require_permission("addresses:manage"))]
AddressService = Annotated[ListAddressesServiceInterface, Depends(get_service)]


@router.get("/me/addresses", response_model=list[ListAddressesResponse])
def list_my_addresses(
    current_user: AddressOwner, service: AddressService
) -> list[ListAddressesResponse]:
    """List delivery addresses in creation order."""
    return service.execute(current_user.id)
