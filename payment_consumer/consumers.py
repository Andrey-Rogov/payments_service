from logging import getLogger
from faststream import AckPolicy
from faststream.rabbit import RabbitBroker

from models import PaymentStatus, OutboxEvent, WebhookResponse
from config import get_settings
from repository import MessageRepository
from service import MessageService, MessageProducer

settings = get_settings()
logger = getLogger("output")

rabbit = RabbitBroker(settings.rabbitmq_url)
producer = MessageProducer(rabbit)
service = MessageService(MessageRepository(), producer)


@rabbit.subscriber(
    producer.payment_queue,
    exchange=producer.payment_exchange,
    ack_policy=AckPolicy.NACK_ON_ERROR
)
async def process_payment_message(msg: dict):
    """
    Consumer для очереди новых платежей. После проверки идемпотентности мулирует процесс оплаты и обновляет
    статус платежа. Затем отправляет webhook на основное FastAPI приложение
    """
    payment_message = OutboxEvent.model_validate(msg)
    logger.info(f'Got message: {payment_message}')
    already_processed = await service.message_idempotency_check(payment_message)
    if already_processed:
        logger.info(f'already_processed')
        return

    logger.info(f"Processing payment ...{payment_message.event_id[-5:]}")
    payment_status = await service.process_payment(OutboxEvent.model_validate(msg))

    logger.info('Sending webhook...')
    await service.send_webhook(
        payment_message.webhook_url,
        WebhookResponse(
            payment_id=payment_message.event_id,
            state=payment_status
        )
    )


@rabbit.subscriber(
    producer.payment_dlq,
    exchange=producer.payment_dlx
)
async def dlq_process(msg: dict):
    """
    Consumer DLQ. Обновляет статус у необработанных по TTL / упавших после retry платежей на FAILED
    """
    logger.info(f'DLQ received a message: {msg}\nSetting status to FAILED')

    payment_message = OutboxEvent.model_validate(msg)
    await service.update_payment_status(PaymentStatus.FAILED, payment_message.event_id)
