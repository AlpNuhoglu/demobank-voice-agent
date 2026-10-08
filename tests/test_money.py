from decimal import Decimal

import pytest

from app.money import format_try, from_kurus, to_kurus


@pytest.mark.parametrize(
    ("amount", "kurus"),
    [(Decimal("1250.50"), 125050), (Decimal("0.01"), 1), (Decimal("45"), 4500)],
)
def test_kurus_round_trip(amount: Decimal, kurus: int) -> None:
    assert to_kurus(amount) == kurus
    assert from_kurus(kurus) == amount


def test_to_kurus_rounds_half_up() -> None:
    assert to_kurus(Decimal("10.005")) == 1001


@pytest.mark.parametrize(
    ("amount", "text"),
    [
        (Decimal("1250.50"), "1.250,50 TL"),
        (Decimal("45"), "45,00 TL"),
        (Decimal("1234567.8"), "1.234.567,80 TL"),
    ],
)
def test_format_try(amount: Decimal, text: str) -> None:
    assert format_try(amount) == text
