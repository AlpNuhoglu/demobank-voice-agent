from datetime import UTC, date, datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import TIMEZONE
from app.db import Base


class IstanbulDateTime(TypeDecorator[datetime]):
    """Stores UTC (SQLite has no time zones) and returns aware Europe/Istanbul datetimes."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetimes are not allowed")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC).astimezone(TIMEZONE)


class CardType(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class CardStatus(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class BlockReason(StrEnum):
    LOST = "lost"
    STOLEN = "stolen"
    OTHER = "other"


def _enum(cls: type[StrEnum]) -> Enum:
    return Enum(cls, native_enum=False, values_callable=lambda e: [m.value for m in e])


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (CheckConstraint("phone_number LIKE '+90%'", name="phone_e164_tr"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(100))
    phone_number: Mapped[str] = mapped_column(String(16), unique=True, index=True)

    cards: Mapped[list["Card"]] = relationship(back_populates="customer", order_by="Card.id")

    def __repr__(self) -> str:  # never include the phone number
        return f"Customer(id={self.id})"


class Card(Base):
    __tablename__ = "cards"
    __table_args__ = (CheckConstraint("length(last4) = 4", name="last4_len"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    type: Mapped[CardType] = mapped_column(_enum(CardType))
    last4: Mapped[str] = mapped_column(String(4))
    status: Mapped[CardStatus] = mapped_column(_enum(CardStatus))
    expires_on: Mapped[date] = mapped_column(Date)
    blocked_at: Mapped[datetime | None] = mapped_column(IstanbulDateTime)
    block_reason: Mapped[BlockReason | None] = mapped_column(_enum(BlockReason))

    customer: Mapped[Customer] = relationship(back_populates="cards")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="card", order_by="Transaction.occurred_at"
    )

    def __repr__(self) -> str:
        return f"Card(id={self.id}, last4={self.last4}, status={self.status})"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    merchant: Mapped[str] = mapped_column(String(100))
    amount_kurus: Mapped[int]
    occurred_at: Mapped[datetime] = mapped_column(IstanbulDateTime, index=True)
    category: Mapped[str] = mapped_column(String(30))

    card: Mapped[Card] = relationship(back_populates="transactions")
