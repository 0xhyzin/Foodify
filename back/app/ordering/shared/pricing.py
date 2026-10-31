"""Money calculations and explicit cart limits, independent of HTTP and SQL."""

from decimal import ROUND_HALF_UP, Decimal

MAX_CART_LINES = 50
MAX_QUANTITY = 99
MAX_TOTAL = Decimal("9999999999.99")
ZERO = Decimal("0.00")


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
