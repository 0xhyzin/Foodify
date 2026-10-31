from typing import Protocol

from .dto import PaymentMethodsResponse


class ListMethodsServiceInterface(Protocol):
    def execute(self) -> PaymentMethodsResponse: ...
