"""Explicit development simulation; production has no pretend successful charge."""

from decimal import Decimal
from uuid import uuid4

from app.core.config import Settings
from app.ordering.shared.interfaces import PaymentResult
from app.shared.errors import AppError


class ConfiguredPaymentGateway:
    """Prepare payment state; external authorisation happens through hosted checkout."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def methods(self) -> list[dict]:
        s = self.settings
        ready = bool(s.paymob_secret_key and s.paymob_public_key and s.paymob_hmac_secret)
        return [
            {
                "code": "card",
                "label": "Visa / Mastercard",
                "enabled": ready and bool(s.paymob_card_integration_id),
                "recipient": None,
            },
            {
                "code": "vodafone_cash",
                "label": "فودافون كاش",
                "enabled": ready and bool(s.paymob_wallet_integration_id),
                "recipient": None,
            },
            {
                "code": "orange_cash",
                "label": "أورانج كاش",
                "enabled": ready and bool(s.paymob_wallet_integration_id),
                "recipient": None,
            },
            {
                "code": "instapay",
                "label": "InstaPay — تحويل يُراجع يدويًا",
                "enabled": bool(s.instapay_recipient and s.instapay_recipient_name),
                "recipient": s.instapay_recipient,
                "recipient_name": s.instapay_recipient_name,
            },
            {
                "code": "cash",
                "label": "الدفع عند الاستلام",
                "enabled": s.allow_cash_on_delivery,
                "recipient": None,
            },
            {
                "code": "simulated",
                "label": "محاكاة تطوير فقط",
                "enabled": s.app_env != "production" and s.allow_simulated_payments,
                "recipient": None,
            },
        ]

    def authorize(self, amount: Decimal, method: str) -> PaymentResult:
        code = "simulated" if method == "sandbox" else method
        if amount <= 0 or not any(m["code"] == code and m["enabled"] for m in self.methods()):
            raise AppError(
                "payment_method_unavailable",
                "This payment method is not configured or enabled.",
                503,
            )
        if code == "simulated":
            return SimulatedPaymentGateway(
                self.settings.app_env, self.settings.allow_simulated_payments
            ).authorize(amount, method)
        provider = (
            "cash" if code == "cash" else "manual_transfer" if code == "instapay" else "paymob"
        )
        status = (
            "due_on_delivery"
            if code == "cash"
            else "awaiting_transfer"
            if code == "instapay"
            else "pending"
        )
        return PaymentResult(
            provider=provider,
            status=status,
            reference=str(uuid4()),
            test_mode=provider == "paymob" and not self.settings.paymob_live,
            recipient=self.settings.instapay_recipient if code == "instapay" else None,
            recipient_name=self.settings.instapay_recipient_name if code == "instapay" else None,
        )


class SimulatedPaymentGateway:
    def __init__(self, environment: str, enabled: bool) -> None:
        self.environment = environment
        self.enabled = enabled

    def authorize(self, amount: Decimal, method: str) -> PaymentResult:
        if self.environment == "production" or not self.enabled:
            raise AppError(
                "payment_provider_unavailable",
                "No live payment provider is configured. Checkout is unavailable.",
                503,
            )
        if method not in {"simulated", "sandbox"} or amount < 0:
            raise AppError("invalid_payment", "The payment request is invalid.", 422)
        return PaymentResult(provider="simulation", status="simulated", reference=str(uuid4()))
