from app.payments.shared.interfaces import PaymentMethods

from .dto import PaymentMethodsData, PaymentMethodsResponse


class ListMethodsService:
    def __init__(self, methods: PaymentMethods) -> None:
        self.methods = methods

    def execute(self) -> PaymentMethodsResponse:
        return PaymentMethodsResponse(data=PaymentMethodsData(methods=self.methods.methods()))
