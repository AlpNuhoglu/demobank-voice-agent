"""Deterministic, idempotent synthetic seed data. Everything here is fictional."""

import random
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.config import TIMEZONE
from app.db import reset_db
from app.models import BlockReason, Card, CardStatus, CardType, Customer, Transaction

SEED = 42
WINDOW_DAYS = 30

# Obviously synthetic: same prefix, last digits 0001-0005.
PHONE_PREFIX = "+90555000"

CUSTOMER_NAMES = [
    "Ayşe Demir",
    "Mehmet Kaya",
    "Zeynep Arslan",
    "Emre Çelik",
    "Elif Şahin",
]

# (status, type) per customer. One expired, one blocked card in total.
CARD_PLAN: list[list[tuple[CardStatus, CardType]]] = [
    [(CardStatus.ACTIVE, CardType.DEBIT), (CardStatus.ACTIVE, CardType.CREDIT)],
    [(CardStatus.ACTIVE, CardType.DEBIT)],
    [(CardStatus.ACTIVE, CardType.CREDIT), (CardStatus.EXPIRED, CardType.DEBIT)],
    [(CardStatus.BLOCKED, CardType.CREDIT), (CardStatus.ACTIVE, CardType.DEBIT)],
    [(CardStatus.ACTIVE, CardType.DEBIT)],
]

# Fictional merchants: (name, category, min TL, max TL).
MERCHANTS: list[tuple[str, str, int, int]] = [
    ("Demo Market", "market", 85, 1_450),
    ("Komşu Bakkal", "market", 25, 320),
    ("Kuzey Kahve", "restoran", 45, 180),
    ("Lezzet Durağı Lokantası", "restoran", 180, 950),
    ("Anadolu Akaryakıt", "akaryakıt", 600, 2_800),
    ("Boğaz Eczanesi", "eczane", 60, 750),
    ("Moda Rüzgarı Giyim", "giyim", 350, 3_200),
    ("Kent Enerji Fatura", "fatura", 280, 1_900),
    ("Hızlı Sepet E-Ticaret", "e-ticaret", 120, 4_500),
    ("Yıldız Elektronik", "elektronik", 450, 4_500),
    ("Sahil Sinema", "eğlence", 140, 600),
]


@dataclass(frozen=True)
class SeedSummary:
    customers: int
    cards: int
    transactions: int


def istanbul_now() -> datetime:
    return datetime.now(TIMEZONE)


def _amount_kurus(rng: random.Random, low_tl: int, high_tl: int) -> int:
    lira = rng.randint(low_tl, high_tl - 1)
    # Mostly round-ish amounts with some odd kurus, as real receipts look.
    kurus = rng.choice([0, 0, 50, 90, rng.randint(1, 99)])
    return lira * 100 + kurus


def _occurred_at(rng: random.Random, start: datetime, end: datetime) -> datetime:
    span = int((end - start).total_seconds())
    moment = start + timedelta(seconds=rng.randint(0, span))
    # Keep activity in waking hours (08:00-23:00 Istanbul time).
    local = moment.astimezone(TIMEZONE)
    local = local.replace(hour=8 + local.hour % 15, microsecond=0)
    return min(max(local, start), end)


def build(now: datetime) -> list[Customer]:
    """Build the full object graph for a given reference time, without touching the DB."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(TIMEZONE).replace(microsecond=0)
    rng = random.Random(SEED)
    window_start = now - timedelta(days=WINDOW_DAYS)
    today = now.date()

    customers: list[Customer] = []
    used_last4: set[str] = set()
    for idx, (name, plan) in enumerate(zip(CUSTOMER_NAMES, CARD_PLAN, strict=True), start=1):
        customer = Customer(full_name=name, phone_number=f"{PHONE_PREFIX}{idx:04d}")
        for status, card_type in plan:
            last4 = f"{rng.randint(0, 9999):04d}"
            while last4 in used_last4:
                last4 = f"{rng.randint(0, 9999):04d}"
            used_last4.add(last4)

            card = Card(type=card_type, last4=last4, status=status)
            tx_end = now
            if status is CardStatus.EXPIRED:
                # Expired mid-window: transactions happen only before expiry.
                card.expires_on = today - timedelta(days=rng.randint(8, 15))
                tx_end = datetime.combine(card.expires_on, time.min, TIMEZONE) - timedelta(
                    seconds=1
                )
            else:
                card.expires_on = date(today.year + rng.randint(1, 4), rng.randint(1, 12), 1)
            if status is CardStatus.BLOCKED:
                card.blocked_at = now - timedelta(days=2, hours=rng.randint(0, 12), minutes=17)
                card.block_reason = BlockReason.LOST
                tx_end = card.blocked_at

            for _ in range(rng.randint(8, 15)):
                merchant, category, low, high = rng.choice(MERCHANTS)
                card.transactions.append(
                    Transaction(
                        merchant=merchant,
                        category=category,
                        amount_kurus=_amount_kurus(rng, low, high),
                        occurred_at=_occurred_at(rng, window_start, tx_end),
                    )
                )
            customer.cards.append(card)
        customers.append(customer)
    return customers


def seed(engine: Engine, now: datetime | None = None) -> SeedSummary:
    """Drop all tables, recreate them and insert the synthetic data set."""
    reset_db(engine)
    customers = build(now or istanbul_now())
    with Session(engine) as session:
        session.add_all(customers)
        session.commit()
        cards = [c for cust in customers for c in cust.cards]
        return SeedSummary(
            customers=len(customers),
            cards=len(cards),
            transactions=sum(len(c.transactions) for c in cards),
        )
