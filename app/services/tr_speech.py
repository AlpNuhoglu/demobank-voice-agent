"""Turn values into the words a Turkish speaker says aloud.

The voice agent reads these strings verbatim, so no digit is ever left for the
LLM or the TTS engine to interpret.
"""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.config import TIMEZONE

_ONES = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
_TENS = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
_DIGITS = ["sıfır", *_ONES[1:]]
_MONTHS = [
    "Ocak",
    "Şubat",
    "Mart",
    "Nisan",
    "Mayıs",
    "Haziran",
    "Temmuz",
    "Ağustos",
    "Eylül",
    "Ekim",
    "Kasım",
    "Aralık",
]

MAX_INT = 999_999_999
MAX_AMOUNT = Decimal("999999999.99")
_KURUS = Decimal("0.01")


def _group_words(n: int) -> list[str]:
    """Words for 1-999. Hundreds never take "bir": 100 is "yüz"."""
    hundreds, rest = divmod(n, 100)
    tens, ones = divmod(rest, 10)
    words: list[str] = []
    if hundreds:
        if hundreds > 1:
            words.append(_ONES[hundreds])
        words.append("yüz")
    if tens:
        words.append(_TENS[tens])
    if ones:
        words.append(_ONES[ones])
    return words


def _int_to_words(n: int) -> str:
    if not 0 <= n <= MAX_INT:
        raise ValueError(f"out of range 0..{MAX_INT}")
    if n == 0:
        return "sıfır"
    millions, rest = divmod(n, 1_000_000)
    thousands, units = divmod(rest, 1_000)
    words: list[str] = []
    if millions:
        words += [*_group_words(millions), "milyon"]
    if thousands:
        # 1000 is "bin", never "bir bin".
        words += ["bin"] if thousands == 1 else [*_group_words(thousands), "bin"]
    if units:
        words += _group_words(units)
    return " ".join(words)


def amount_to_speech(amount: Decimal | int) -> str:
    """Decimal("1250.50") -> "bin iki yüz elli lira elli kuruş"."""
    if isinstance(amount, bool) or not isinstance(amount, Decimal | int):
        raise TypeError("amount must be Decimal or int")
    amount = Decimal(amount)
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    amount = amount.quantize(_KURUS, rounding=ROUND_HALF_UP)
    if amount < 0 or amount > MAX_AMOUNT:
        raise ValueError(f"amount out of range 0..{MAX_AMOUNT}")

    lira = int(amount)
    kurus = int((amount - lira) * 100)
    parts: list[str] = []
    if lira or not kurus:
        parts.append(f"{_int_to_words(lira)} lira")
    if kurus:
        parts.append(f"{_int_to_words(kurus)} kuruş")
    return " ".join(parts)


def _istanbul_date(value: datetime | date, name: str) -> date:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"{name} must be timezone-aware")
        return value.astimezone(TIMEZONE).date()
    return value


def date_to_speech(dt: datetime | date, now: datetime | None = None) -> str:
    """ "bugün", "dün", "üç Ekim" (current year) or "üç Ekim iki bin yirmi beş"."""
    day = _istanbul_date(dt, "dt")
    today = _istanbul_date(now or datetime.now(TIMEZONE), "now")

    delta = (today - day).days
    if delta == 0:
        return "bugün"
    if delta == 1:
        return "dün"
    spoken = f"{_int_to_words(day.day)} {_MONTHS[day.month - 1]}"
    if day.year != today.year:
        spoken += f" {_int_to_words(day.year)}"
    return spoken


def digits_to_speech(digits: str) -> str:
    """ "4007" -> "dört sıfır sıfır yedi". Spaces are ignored."""
    compact = digits.replace(" ", "")
    if not compact or not (compact.isascii() and compact.isdigit()):
        raise ValueError("expected a non-empty string of digits")
    return " ".join(_DIGITS[int(c)] for c in compact)
