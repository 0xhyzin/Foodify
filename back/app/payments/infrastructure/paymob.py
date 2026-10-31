"""Egypt Intention API + hosted checkout. Never receives PAN, CVV or OTP.

Official contracts: developers.paymob.com/paymob-docs/intention-apis/create-intention
and developers/webhook-callbacks-and-hmac/hmac/hmac-transaction-callback.
"""

import hashlib
import hmac
import re
from datetime import timedelta
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.ordering.models import FoodOrder
from app.payments.shared.interfaces import HostedCheckout, VerifiedTransaction
from app.shared.errors import AppError
from app.shared.time import utcnow

HMAC_FIELDS = (
    "amount_cents",
    "created_at",
    "currency",
    "error_occured",
    "has_parent_transaction",
    "id",
    "integration_id",
    "is_3d_secure",
    "is_auth",
    "is_capture",
    "is_refunded",
    "is_standalone_payment",
    "is_voided",
    "order.id",
    "owner",
    "pending",
    "source_data.pan",
    "source_data.sub_type",
    "source_data.type",
    "success",
)


class PaymobHostedGateway:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.cipher = Fernet(settings.email_encryption_key.get_secret_value().encode())

    def integration_id(self, method: str) -> int:
        s = self.settings
        value = s.paymob_card_integration_id if method == "card" else s.paymob_wallet_integration_id
        if not value or not (s.paymob_secret_key and s.paymob_public_key and s.paymob_hmac_secret):
            raise AppError(
                "payment_method_unavailable", "Paymob is not configured for this method.", 503
            )
        return value

    def checkout_url(self, encrypted_token: str) -> str:
        token = self.cipher.decrypt(encrypted_token.encode()).decode()
        return "https://accept.paymob.com/unifiedcheckout/?" + urlencode(
            {"publicKey": self.settings.paymob_public_key, "clientSecret": token}
        )

    def create_checkout(self, order: FoodOrder, email: str) -> HostedCheckout:
        integration = self.integration_id(order.payment_method)
        address = order.delivery_address
        names = address["recipient_name"].split(maxsplit=1)
        items = [
            {
                "name": item.item_name,
                "amount": int(item.unit_price * 100),
                "quantity": item.quantity,
            }
            for item in order.items
        ]
        if order.delivery_fee:
            items.append(
                {"name": "Delivery", "amount": int(order.delivery_fee * 100), "quantity": 1}
            )
        body = {
            "amount": int(order.total * 100),
            "currency": order.currency,
            "payment_methods": [integration],
            "items": items,
            "billing_data": {
                "first_name": names[0],
                "last_name": names[1] if len(names) > 1 else names[0],
                "email": email,
                "phone_number": address["phone"],
                "country": address["country_code"],
                "city": address["city"],
                "state": address["area"],
                "street": address["street"],
                "building": address["building"],
                "floor": address.get("floor") or "NA",
                "apartment": address.get("apartment") or "NA",
            },
            "special_reference": order.payment.reference,
            "expiration": 3600,
            "notification_url": self.settings.public_base_url.rstrip("/")
            + "/api/v1/payments/paymob/callback",
            "redirection_url": self.settings.public_base_url.rstrip("/")
            + "/api/v1/payments/return/"
            + order.id,
        }
        try:
            # Fixed origin, TLS verification, bounded timeout, no redirects or automatic POST retry.
            with httpx.Client(timeout=20, follow_redirects=False) as client:
                response = client.post(
                    "https://accept.paymob.com/v1/intention/",
                    json=body,
                    headers={
                        "Authorization": "Token "
                        + self.settings.paymob_secret_key.get_secret_value()
                    },
                )
                response.raise_for_status()
                data = response.json()
            token, intention, provider_order = (
                data["client_secret"],
                data["id"],
                data["intention_order_id"],
            )
            if (
                not isinstance(token, str)
                or not token
                or not isinstance(intention, str)
                or type(provider_order) is not int
            ):
                raise ValueError("Invalid intention response")
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            # An uncertain response must not create a second potentially chargeable intention.
            raise AppError(
                "payment_initialization_unknown",
                "Could not confirm payment setup. Do not submit again; "
                "contact support with your order number.",
                503,
            ) from None
        encrypted = self.cipher.encrypt(token.encode()).decode()
        return HostedCheckout(
            str(provider_order),
            intention,
            encrypted,
            utcnow() + timedelta(hours=1),
            self.checkout_url(encrypted),
        )

    def verify_callback(self, payload: dict, signature: str) -> VerifiedTransaction:
        secret = self.settings.paymob_hmac_secret
        if not secret or not re.fullmatch(r"[a-fA-F0-9]{128}", signature):
            raise AppError("invalid_payment_signature", "Invalid payment signature.", 401)
        if payload.get("type") != "TRANSACTION" or not isinstance(payload.get("obj"), dict):
            raise AppError(
                "invalid_payment_callback", "Only transaction callbacks are supported.", 422
            )
        obj = payload["obj"]
        try:
            values = []
            for path in HMAC_FIELDS:
                value = obj
                for key in path.split("."):
                    value = value[key]
                if value is not None and not isinstance(value, (str, bool, int)):
                    raise ValueError()
                values.append(
                    ""
                    if value is None
                    else str(value).lower()
                    if isinstance(value, bool)
                    else str(value)
                )
            expected = hmac.new(
                secret.get_secret_value().encode(), "".join(values).encode(), hashlib.sha512
            ).hexdigest()
            if not hmac.compare_digest(expected, signature.lower()):
                raise AppError("invalid_payment_signature", "Invalid payment signature.", 401)
            for flag in (
                "success",
                "pending",
                "is_refunded",
                "is_voided",
                "error_occured",
                "is_auth",
                "is_capture",
                "is_standalone_payment",
            ):
                if type(obj[flag]) is not bool:
                    raise ValueError()
            for number in (
                obj["id"],
                obj["amount_cents"],
                obj["integration_id"],
                obj["order"]["id"],
            ):
                if type(number) is not int or number < 0:
                    raise ValueError()
            # is_live isn't part of the signed field list: never rely on it for authentication.
            status = (
                "refunded"
                if obj["is_refunded"] or obj["is_voided"]
                else "pending"
                if obj["pending"]
                else "paid"
                if obj["success"]
                and not obj["error_occured"]
                and (obj["is_capture"] or obj["is_standalone_payment"])
                and not obj["is_auth"]
                else "failed"
            )
            return VerifiedTransaction(
                str(obj["id"]),
                str(obj["order"]["id"]),
                obj["amount_cents"],
                obj["currency"],
                obj["integration_id"],
                status,
            )
        except (KeyError, TypeError, ValueError):
            raise AppError(
                "invalid_payment_callback", "Invalid transaction callback.", 422
            ) from None
