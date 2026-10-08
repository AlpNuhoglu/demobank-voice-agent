import re
from collections import Counter
from datetime import timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import TIMEZONE
from app.models import BlockReason, Card, CardStatus, Customer, Transaction
from app.schemas import CardOut, TransactionOut
from app.services.seed import WINDOW_DAYS, build, seed
from tests.conftest import REFERENCE_NOW

E164 = re.compile(r"^\+90\d{10}$")


def _snapshot(engine) -> list[tuple]:
    with Session(engine) as s:
        rows = s.execute(
            select(
                Customer.full_name,
                Customer.phone_number,
                Card.last4,
                Card.status,
                Card.expires_on,
                Card.blocked_at,
                Transaction.merchant,
                Transaction.amount_kurus,
                Transaction.occurred_at,
            )
            .join(Card, Card.customer_id == Customer.id)
            .join(Transaction, Transaction.card_id == Card.id)
            .order_by(Transaction.id)
        )
        return [tuple(r) for r in rows]


def test_seed_counts(engine) -> None:
    summary = seed(engine, REFERENCE_NOW)
    with Session(engine) as s:
        assert s.scalar(select(func.count(Customer.id))) == 5 == summary.customers
        cards = s.scalars(select(Card)).all()
        assert len(cards) == summary.cards
        per_customer = Counter(c.customer_id for c in cards)
        assert all(1 <= n <= 2 for n in per_customer.values())
        for card in cards:
            assert 8 <= len(card.transactions) <= 15
        assert s.scalar(select(func.count(Transaction.id))) == summary.transactions


def test_seed_is_idempotent_and_deterministic(engine) -> None:
    seed(engine, REFERENCE_NOW)
    first = _snapshot(engine)
    seed(engine, REFERENCE_NOW)
    assert _snapshot(engine) == first
    assert len(first) > 0


def test_card_statuses_and_expiry(engine) -> None:
    seed(engine, REFERENCE_NOW)
    today = REFERENCE_NOW.date()
    with Session(engine) as s:
        cards = s.scalars(select(Card)).all()
        statuses = Counter(c.status for c in cards)
        assert statuses[CardStatus.EXPIRED] == 1
        assert statuses[CardStatus.BLOCKED] == 1

        for card in cards:
            out = CardOut.model_validate(card)
            assert out.expires_on == card.expires_on
            if card.status is CardStatus.EXPIRED:
                assert card.expires_on < today
                assert all(t.occurred_at.date() < card.expires_on for t in card.transactions)
            else:
                assert card.expires_on > today
            if card.status is CardStatus.BLOCKED:
                assert card.block_reason is BlockReason.LOST
                assert card.blocked_at is not None and card.blocked_at < REFERENCE_NOW
                assert out.block_reason == "lost"
            else:
                assert card.blocked_at is None and card.block_reason is None


def test_customers_are_synthetic_and_unique(engine) -> None:
    seed(engine, REFERENCE_NOW)
    with Session(engine) as s:
        phones = s.scalars(select(Customer.phone_number)).all()
        assert len(set(phones)) == len(phones)
        assert all(E164.match(p) for p in phones)
        assert sorted(phones) == [f"+90555000000{i}" for i in range(1, 6)]
        last4s = s.scalars(select(Card.last4)).all()
        assert len(set(last4s)) == len(last4s)


def test_transactions_within_window_and_tz_aware(engine) -> None:
    seed(engine, REFERENCE_NOW)
    start = REFERENCE_NOW - timedelta(days=WINDOW_DAYS)
    with Session(engine) as s:
        for tx in s.scalars(select(Transaction)):
            assert tx.occurred_at.tzinfo is not None
            assert tx.occurred_at.utcoffset() == REFERENCE_NOW.utcoffset()
            assert start <= tx.occurred_at <= REFERENCE_NOW
            assert tx.amount_kurus > 0
            assert TransactionOut.model_validate(tx).amount > 0


def test_build_rejects_naive_now() -> None:
    with pytest.raises(ValueError):
        build(REFERENCE_NOW.replace(tzinfo=None))


def test_reference_time_is_istanbul() -> None:
    assert REFERENCE_NOW.tzinfo is TIMEZONE
