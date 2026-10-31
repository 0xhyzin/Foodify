from typing import Annotated

from fastapi import Depends

from app.core.config import get_settings
from app.ordering.infrastructure.payments import ConfiguredPaymentGateway
from app.payments.infrastructure.paymob import PaymobHostedGateway
from app.payments.shared.interfaces import HostedPaymentGateway, PaymentMethods


def get_hosted_gateway() -> HostedPaymentGateway:
    return PaymobHostedGateway(get_settings())


def get_payment_methods() -> PaymentMethods:
    return ConfiguredPaymentGateway(get_settings())


HostedGateway = Annotated[HostedPaymentGateway, Depends(get_hosted_gateway)]
Methods = Annotated[PaymentMethods, Depends(get_payment_methods)]
