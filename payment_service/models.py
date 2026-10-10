import enum
import uuid

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class Currency(str, enum.Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"



class PaymentORMSchema(Base):
    __tablename__ = "payments"

    payment_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    amount: Mapped[float] = mapped_column(
        Numeric,
        nullable=False,
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="payment_currency"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    payment_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )
    webhook_url: Mapped[str | None] = mapped_column(
        String(2048),
        server_default="http://payment_service:8000/api/v1/payments/notify"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

class OutboxORMSchema(Base):
    __tablename__ = "outbox"

    event_id: Mapped[str] = mapped_column(
        Text,
        primary_key=True
    )
    event_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    webhook_url: Mapped[str | None] = mapped_column(
        String(2048),
        server_default="http://payment_service:8000/api/v1/payments/notify"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )


class PaymentBase(BaseModel):
    payment_id: str
    amount: float
    currency: Currency
    description: str
    payment_metadata: dict[str, Any] = Field(default_factory=dict)
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str | None = "http://payment_service:8000/api/v1/payments/notify"
    created_at: datetime = datetime.now()
    processed_at: datetime | None = None
