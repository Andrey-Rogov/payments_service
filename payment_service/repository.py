import datetime

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from collections.abc import AsyncGenerator

from models import PaymentORMSchema, OutboxORMSchema, PaymentStatus
from config import get_settings
from schemas import CreatePaymentResponse

settings = get_settings()
async_engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker[AsyncSession](bind=async_engine, expire_on_commit=False, autoflush=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_payment(self, payment_id: str) -> PaymentORMSchema | None:
        payment = await self.session.get(PaymentORMSchema, payment_id)
        return payment

    async def get_payment_by_idempotency_key(self, idempotency_key: str) -> PaymentORMSchema | None:
        query = select(PaymentORMSchema).where(
            PaymentORMSchema.idempotency_key == idempotency_key
        )
        result = await self.session.execute(query)
        payment = result.scalar_one_or_none()
        return payment

    async def create_payment(
        self,
        payment: PaymentORMSchema,
        outbox_event: OutboxORMSchema,
        idempotency_key: str
    ):
        query = (
            insert(PaymentORMSchema).values(
                amount=payment.amount,
                currency=payment.currency,
                description=payment.description,
                idempotency_key=idempotency_key,
                payment_metadata=payment.payment_metadata
            ).on_conflict_do_nothing(
                index_elements=["idempotency_key"]
            ).returning(
                PaymentORMSchema.payment_id
            )
        )
        result = await self.session.execute(query)
        payment_id = result.scalar_one_or_none()
        if payment_id:
            outbox_event.event_id = payment_id
            self.session.add(outbox_event)
            await self.session.commit()
            return CreatePaymentResponse(
                payment_id=payment_id,
                status=PaymentStatus.PENDING,
                created_at=datetime.datetime.now(),

            )
        else:
            existing_payment = await self.get_payment_by_idempotency_key(idempotency_key)
            return CreatePaymentResponse.model_validate(existing_payment)


def get_payment_repository(
    session: AsyncSession = Depends(get_db),
) -> PaymentRepository:
    return PaymentRepository(session)
