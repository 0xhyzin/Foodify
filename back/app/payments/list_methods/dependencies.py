from app.payments.shared.dependencies import Methods

from .interfaces import ListMethodsServiceInterface
from .service import ListMethodsService


def get_service(methods: Methods) -> ListMethodsServiceInterface:
    return ListMethodsService(methods)
