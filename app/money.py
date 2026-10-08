"""Money helpers. Amounts are Decimal TRY in code and integer kurus in the DB."""

from decimal import ROUND_HALF_UP, Decimal

_KURUS = Decimal("0.01")


def to_kurus(amount: Decimal) -> int:
    return int((amount.quantize(_KURUS, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def from_kurus(kurus: int) -> Decimal:
    return (Decimal(kurus) / 100).quantize(_KURUS)


def format_try(amount: Decimal) -> str:
    """Format as Turkish lira, e.g. Decimal("1250.50") -> "1.250,50 TL"."""
    text = f"{amount.quantize(_KURUS, rounding=ROUND_HALF_UP):,.2f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".") + " TL"
