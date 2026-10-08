from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.config import TIMEZONE
from app.services.tr_speech import (
    _int_to_words,
    amount_to_speech,
    date_to_speech,
    digits_to_speech,
)

NOW = datetime(2026, 10, 8, 15, 30, tzinfo=TIMEZONE)


@pytest.mark.parametrize(
    ("n", "words"),
    [
        (0, "sıfır"),
        (1, "bir"),
        (10, "on"),
        (11, "on bir"),
        (100, "yüz"),
        (101, "yüz bir"),
        (999, "dokuz yüz doksan dokuz"),
        (1000, "bin"),
        (1001, "bin bir"),
        (2000, "iki bin"),
        (10_000, "on bin"),
        (100_000, "yüz bin"),
        (101_101, "yüz bir bin yüz bir"),
        (1_000_000, "bir milyon"),
        (1_000_001, "bir milyon bir"),
        (1_001_000, "bir milyon bin"),
        (2_000_000, "iki milyon"),
        (2025, "iki bin yirmi beş"),
        (
            999_999_999,
            "dokuz yüz doksan dokuz milyon dokuz yüz doksan dokuz bin dokuz yüz doksan dokuz",
        ),
    ],
)
def test_int_to_words(n: int, words: str) -> None:
    assert _int_to_words(n) == words


@pytest.mark.parametrize(
    ("amount", "speech"),
    [
        (Decimal("0"), "sıfır lira"),
        (Decimal("1"), "bir lira"),
        (Decimal("10"), "on lira"),
        (Decimal("11"), "on bir lira"),
        (Decimal("100"), "yüz lira"),
        (Decimal("101"), "yüz bir lira"),
        (Decimal("1000"), "bin lira"),
        (Decimal("1001"), "bin bir lira"),
        (Decimal("1250.50"), "bin iki yüz elli lira elli kuruş"),
        (Decimal("2000000"), "iki milyon lira"),
        (Decimal("1000000"), "bir milyon lira"),
        (Decimal("0.75"), "yetmiş beş kuruş"),
        (Decimal("0.01"), "bir kuruş"),
        (Decimal("0.99"), "doksan dokuz kuruş"),
        (Decimal("1.01"), "bir lira bir kuruş"),
        (Decimal("99.99"), "doksan dokuz lira doksan dokuz kuruş"),
        (Decimal("1000.10"), "bin lira on kuruş"),
        (Decimal("10.005"), "on lira bir kuruş"),  # half-up rounding
        (Decimal("0.004"), "sıfır lira"),
        (250, "iki yüz elli lira"),
        (
            Decimal("999999999.99"),
            "dokuz yüz doksan dokuz milyon dokuz yüz doksan dokuz bin dokuz yüz doksan dokuz "
            "lira doksan dokuz kuruş",
        ),
    ],
)
def test_amount_to_speech(amount: Decimal | int, speech: str) -> None:
    assert amount_to_speech(amount) == speech


@pytest.mark.parametrize(
    ("amount", "error"),
    [
        (Decimal("-1"), ValueError),
        (Decimal("1000000000"), ValueError),
        (Decimal("999999999.995"), ValueError),  # rounds above the maximum
        (Decimal("NaN"), ValueError),
        (Decimal("Infinity"), ValueError),
        (12.5, TypeError),
        (True, TypeError),
    ],
)
def test_amount_to_speech_rejects(amount: object, error: type[Exception]) -> None:
    with pytest.raises(error):
        amount_to_speech(amount)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("dt", "now", "speech"),
    [
        (datetime(2026, 10, 8, 9, 0, tzinfo=TIMEZONE), NOW, "bugün"),
        (datetime(2026, 10, 7, 23, 59, tzinfo=TIMEZONE), NOW, "dün"),
        (datetime(2026, 10, 6, 12, 0, tzinfo=TIMEZONE), NOW, "altı Ekim"),
        (datetime(2026, 10, 3, 12, 0, tzinfo=TIMEZONE), NOW, "üç Ekim"),
        (datetime(2026, 1, 1, 0, 0, tzinfo=TIMEZONE), NOW, "bir Ocak"),
        (datetime(2025, 10, 3, 12, 0, tzinfo=TIMEZONE), NOW, "üç Ekim iki bin yirmi beş"),
        (datetime(2025, 12, 31, 12, 0, tzinfo=TIMEZONE), NOW, "otuz bir Aralık iki bin yirmi beş"),
        # Year boundary: yesterday wins over the year check.
        (
            datetime(2025, 12, 31, 20, 0, tzinfo=TIMEZONE),
            datetime(2026, 1, 1, 10, 0, tzinfo=TIMEZONE),
            "dün",
        ),
        # 21:30 UTC on 7 Oct is 00:30 on 8 Oct in Istanbul: still "bugün".
        (datetime(2026, 10, 7, 21, 30, tzinfo=UTC), NOW, "bugün"),
        # 20:30 UTC on 7 Oct is 23:30 on 7 Oct in Istanbul: "dün".
        (datetime(2026, 10, 7, 20, 30, tzinfo=UTC), NOW, "dün"),
        (date(2026, 9, 15), NOW, "on beş Eylül"),
        # Future dates get no relative word.
        (datetime(2026, 10, 9, 12, 0, tzinfo=TIMEZONE), NOW, "dokuz Ekim"),
    ],
)
def test_date_to_speech(dt: datetime | date, now: datetime, speech: str) -> None:
    assert date_to_speech(dt, now=now) == speech


def test_date_to_speech_defaults_to_real_now() -> None:
    assert date_to_speech(datetime.now(TIMEZONE)) == "bugün"


@pytest.mark.parametrize(
    ("dt", "now"),
    [
        (datetime(2026, 10, 8, 12, 0), NOW),
        (datetime(2026, 10, 8, 12, 0, tzinfo=TIMEZONE), datetime(2026, 10, 8, 15, 30)),
    ],
    ids=["naive-dt", "naive-now"],
)
def test_date_to_speech_rejects_naive(dt: datetime, now: datetime) -> None:
    with pytest.raises(ValueError):
        date_to_speech(dt, now=now)


@pytest.mark.parametrize(
    ("digits", "speech"),
    [
        ("4007", "dört sıfır sıfır yedi"),
        ("0000", "sıfır sıfır sıfır sıfır"),
        ("9", "dokuz"),
        ("1234567890", "bir iki üç dört beş altı yedi sekiz dokuz sıfır"),
        ("40 07", "dört sıfır sıfır yedi"),
    ],
)
def test_digits_to_speech(digits: str, speech: str) -> None:
    assert digits_to_speech(digits) == speech


@pytest.mark.parametrize("digits", ["", "   ", "12a4", "-123", "١٢٣"])
def test_digits_to_speech_rejects(digits: str) -> None:
    with pytest.raises(ValueError):
        digits_to_speech(digits)
