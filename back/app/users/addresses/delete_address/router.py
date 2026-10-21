"""HTTP endpoint for deleting an owned delivery address."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.dependencies import require_permission
from app.infrastructure.models import User
from app.users.addresses.delete_address.dependencies import get_service
from app.users.addresses.delete_address.dto import DeleteAddressCommand
from app.users.addresses.delete_address.interfaces import DeleteAddressServiceInterface

router = APIRouter(tags=["Customer profile"])
AddressOwner = Annotated[User, Depends(require_permission("addresses:manage"))]
AddressService = Annotated[DeleteAddressServiceInterface, Depends(get_service)]


@router.delete("/me/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_address(
    address_id: UUID,
    current_user: AddressOwner,
    service: AddressService,
) -> Response:
    """Delete an address; the oldest remaining address becomes the default."""
    service.execute(DeleteAddressCommand(current_user.id, str(address_id)))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
