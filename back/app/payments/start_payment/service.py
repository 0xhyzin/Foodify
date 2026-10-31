from app.ordering.shared.interfaces import OrderRepository
from app.payments.shared.dto import StartPaymentData, StartPaymentResponse
from app.payments.shared.guards import lock_owned_order
from app.payments.shared.interfaces import HostedPaymentGateway
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class StartPaymentService:
    def __init__(
        self,
        users: UserRepository,
        orders: OrderRepository,
        gateway: HostedPaymentGateway,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.orders, self.gateway, self.uow = users, orders, gateway, uow

    def execute(self, user_id: str, order_id: str) -> StartPaymentResponse:
        order = lock_owned_order(self.users, self.orders, user_id, order_id)
        payment = order.payment
        if not payment or payment.provider != "paymob" or payment.status in {"paid", "refunded"}:
            raise AppError(
                "payment_not_required", "This order cannot start an online payment.", 409
            )
        if payment.checkout_token:
            if not payment.expires_at or payment.expires_at <= utcnow():
                raise AppError(
                    "payment_expired",
                    "The payment link expired. Review your cart and submit a new order.",
                    409,
                )
            response = StartPaymentResponse(
                data=StartPaymentData(
                    order_id=order.id,
                    checkout_url=self.gateway.checkout_url(payment.checkout_token),
                    expires_at=payment.expires_at,
                )
            )
            self.uow.commit()
            return response
        if payment.status != "pending":
            raise AppError(
                "payment_initialization_pending",
                "Payment setup is already running or requires reconciliation. "
                "Contact support with your order number.",
                409,
            )
        self.gateway.integration_id(order.payment_method)
        email = self.users.get_by_id(user_id).email
        payment.status = "initializing"
        self.uow.commit()  # No row lock is held during the external HTTP request.
        try:
            result = self.gateway.create_checkout(order, email)
        except AppError:
            order = lock_owned_order(self.users, self.orders, user_id, order_id)
            if order.payment.status == "initializing":
                order.payment.status = "initialization_unknown"
                self.uow.commit()
            raise
        order = lock_owned_order(self.users, self.orders, user_id, order_id)
        order.payment.provider_order_id = result.provider_order_id
        order.payment.intention_id = result.intention_id
        order.payment.checkout_token = result.encrypted_token
        order.payment.expires_at = result.expires_at
        if order.payment.status == "initializing":
            order.payment.status = "pending"
        response = StartPaymentResponse(
            data=StartPaymentData(
                order_id=order.id, checkout_url=result.url, expires_at=result.expires_at
            )
        )
        self.uow.commit()
        return response
