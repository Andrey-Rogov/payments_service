from contextlib import asynccontextmanager
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from collections.abc import AsyncGenerator
from sqlalchemy.orm import DeclarativeBase

from models import PaymentORMSchema, OutboxORMSchema, PaymentStatus
from config import get_settings

settings = get_settings()
async_engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker[AsyncSession](bind=async_engine, expire_on_commit=False, autoflush=False)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


class MessageRepository:
    async def get_outbox_event(self) -> OutboxORMSchema | None:
        stmt = select(OutboxORMSchema) \
            .where(OutboxORMSchema.sent_at.is_(None)) \
            .limit(1) \
            .with_for_update(skip_locked=True)
        async with get_session() as session:
            result = await session.execute(stmt)
            return result.scalars().first()

    async def update_table_value(self, table_schema: DeclarativeBase, column: str, new_value: Any, filter_args: dict):
        col = getattr(table_schema, column, None)
        if not col:
            raise ValueError(f"Unknown column for {table_schema.__name__} - '{column}'")
        query = (
            update(table_schema).where(
                *[
                    getattr(table_schema, filter_col) == filter_val
                    for filter_col, filter_val in filter_args.items()
                ]
            ).values(
                {column: new_value}
            )
        )
        async with get_session() as session:
            result = await session.execute(query)
            if result.rowcount != 1:
                raise ValueError(f"Row was not updated or filter value included nore than one row")
            await session.commit()

    async def check_is_processed(self, event_id: str) -> bool:
        query = select(PaymentORMSchema).where(
            PaymentORMSchema.payment_id == event_id,
            PaymentORMSchema.status != PaymentStatus.PENDING
        )
        async with get_session() as session:
            result = await session.execute(query)
            is_processed = result.scalar_one_or_none()
            return True if is_processed else False
