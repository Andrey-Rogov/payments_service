import asyncio
import httpx
import random

from logging import getLogger
from datetime import datetime
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue, ExchangeType

from config import get_settings
from repository import MessageRepository
from models import OutboxORMSchema, OutboxEvent, PaymentORMSchema, PaymentStatus, WebhookResponse


logger = getLogger("output")
settings = get_settings()

class MessageProducer:
    def __init__(self, broker: RabbitBroker):
        self.broker = broker
        self.payment_exchange = RabbitExchange(name="payments", auto_delete=True, type=ExchangeType.TOPIC)
        self.payment_queue = RabbitQueue(
            name="payments.payment_created",
            routing_key="payments.*",
            arguments={
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new.dlq",
                "x-queue-type": "quorum",
                "x-delivery-limit": 3
            }
        )
        self.payment_dlx = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT)
        self.payment_dlq = RabbitQueue("payments.dlq", routing_key="payments.new.dlq")

    async def publish_payment_event(self, payload: dict):
        await self.broker.publish(
            payload,
            exchange=self.payment_exchange,
            routing_key="payments.new",
            expiration=60000
        )


class MessageService:
    def __init__(self, repository: MessageRepository, producer: MessageProducer):
        self.repository = repository
        self.producer = producer

    async def update_payment_status(self, new_status: PaymentStatus, payment_id: str):
        await self.repository.update_table_value(
            PaymentORMSchema,
            "status",
            new_status,
            {"payment_id": payment_id}
        )
        await self.repository.update_table_value(
            PaymentORMSchema,
            "processed_at",
            datetime.now(),
            {"payment_id": payment_id}
        )

    async def publish_from_outbox(self) -> PaymentORMSchema | None:
        try:
            message = await self.repository.get_outbox_event()
            if message:
                logger.info(f'Extracted message ...{message.event_id[-5:]} from Outbox')
                payload = OutboxEvent(
                    event_id=message.event_id,
                    event_type=message.event_type,
                    webhook_url=message.webhook_url,
                    created_at=message.created_at,
                )
                await self.producer.publish_payment_event(payload.model_dump())
                logger.info(f'Published message')

                await self.repository.update_table_value(
                    OutboxORMSchema,
                    "sent_at", datetime.now(),
                    {"event_id": message.event_id}
                )
        except Exception as e:
            raise Exception(f"Outbox error: {e}")

    async def message_idempotency_check(self, message: OutboxEvent) -> bool:
        return await self.repository.check_is_processed(message.event_id)

    async def process_payment(self, payment_message: OutboxEvent) -> PaymentStatus:
        # эмуляция оплаты
        await asyncio.sleep(random.randint(2, 5))
        new_status = PaymentStatus.SUCCEEDED if random.random() < 0.9 else PaymentStatus.FAILED

        await self.update_payment_status(new_status, payment_message.event_id)
        logger.info(f"> Payment finished, status - {new_status}")
        return new_status


    @staticmethod
    async def send_webhook(webhook_url: str | None, params: WebhookResponse):
        if webhook_url:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(webhook_url, params=params.model_dump(), timeout=5.0,
                                                 headers={"X-API-Key": settings.api_key})
                    logger.info(f"Webhook response: {response}")
                    response.raise_for_status()

            except Exception as e:
                # Логируем, но не роняем обработку сообщения, так как БД уже обновлена
                logger.info(f"Failed to deliver webhook for {params.payment_id}: {e}")

