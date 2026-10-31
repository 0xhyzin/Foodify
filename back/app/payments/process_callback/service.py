from hashlib import sha256

from app.ordering.models import OrderEvent, PaymentEvent
from app.ordering.shared.interfaces import CartRepository, OrderRepository
from app.payments.shared.guards import lock_owned_order
from app.payments.shared.interfaces import HostedPaymentGateway
from app.payments.shared.state import confirm_paid_order
from app.shared.errors import AppError
from app.shared.ports import UnitOfWork
from app.shared.time import utcnow
from app.users.shared.interfaces import UserRepository


class ProcessCallbackService:
    def __init__(
        self,
        users: UserRepository,
        orders: OrderRepository,
        carts: CartRepository,
        gateway: HostedPaymentGateway,
        uow: UnitOfWork,
    ) -> None:
        self.users, self.orders, self.carts, self.gateway, self.uow = (
            users,
            orders,
            carts,
            gateway,
            uow,
        )

    def execute(self, payload: dict, signature: str) -> None:
        transaction = self.gateway.verify_callback(payload, signature)
        found = self.orders.find_by_provider_order(transaction.provider_order_id)
        if found is None:
            # Non-2xx asks the provider to retry if the intention row hasn't committed yet.
            raise AppError("payment_not_found", "Payment is not available yet.", 503)
        order = lock_owned_order(
            self.users, self.orders, found.user_id, found.id, active_account=False
        )
        payment = order.payment
        if (
            not payment
            or payment.provider != "paymob"
            or transaction.amount_cents != int(order.total * 100)
            or transaction.currency != order.currency
            or transaction.integration_id != self.gateway.integration_id(order.payment_method)
        ):
            raise AppError("payment_mismatch", "Payment does not match the recorded order.", 409)
        event_id = sha256(f"paymob:{transaction.id}:{transaction.status}".encode()).hexdigest()
        if self.orders.has_payment_event(event_id):
            self.uow.commit()
            return
        self.orders.add_payment_event(
            PaymentEvent(
                id=event_id,
                payment_id=payment.id,
                transaction_id=transaction.id,
                status=transaction.status,
                created_at=utcnow(),
            )
        )
        if transaction.status == "refunded":
            if payment.transaction_id and payment.transaction_id != transaction.id:
                raise AppError(
                    "payment_transaction_mismatch",
                    "Refund does not match the settled transaction.",
                    409,
                )
            payment.status = "refunded"
            order.events.append(
                OrderEvent(
                    status=order.status,
                    note="Payment refunded or voided; operational review required.",
                    created_at=utcnow(),
                )
            )
        elif transaction.status == "paid" and payment.status != "refunded":
            if payment.transaction_id and payment.transaction_id != transaction.id:
                raise AppError(
                    "duplicate_payment",
                    "A different transaction already settled this order. "
                    "Reconciliation is required.",
                    409,
                )
            payment.transaction_id = transaction.id
            confirm_paid_order(order, self.carts)
        elif payment.status not in {"paid", "refunded"}:
            payment.status = transaction.status
        self.uow.commit()
