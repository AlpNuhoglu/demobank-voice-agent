from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models import BlockReason, CardStatus, CardType
from app.money import from_kurus


class HealthResponse(BaseModel):
    status: str = "ok"


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str


class CardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    type: CardType
    last4: str
    status: CardStatus
    expires_on: date
    blocked_at: datetime | None
    block_reason: BlockReason | None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    card_id: int
    merchant: str
    amount_kurus: int = Field(exclude=True)
    occurred_at: datetime
    category: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def amount(self) -> Decimal:
        """Amount in TRY."""
        return from_kurus(self.amount_kurus)
