from fastapi import Depends, status, HTTPException

from repository import PaymentRepository, get_payment_repository
from schemas import CreatePaymentRequest, CreatePaymentResponse
from models import PaymentORMSchema, OutboxORMSchema


class PaymentService:
    def __init__(self, repository: PaymentRepository):
        self.repository = repository

    async def get_payment(self, payment_id: str) -> PaymentORMSchema | None:
        payment = await self.repository.get_payment(payment_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Payment '{payment_id}' was not found")
        return payment

    async def create_payment(self, payment: CreatePaymentRequest, idempotency_key: str) -> CreatePaymentResponse:
        payment = PaymentORMSchema(
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            webhook_url=payment.webhook_url,
            idempotency_key=idempotency_key,
            payment_metadata=payment.payment_metadata
        )
        outbox_event = OutboxORMSchema(
            event_id="",
            event_type="payment.created",
            webhook_url=payment.webhook_url
        )
        new_payment = await self.repository.create_payment(payment, outbox_event, idempotency_key)
        return CreatePaymentResponse.model_validate(new_payment.__dict__)


def get_payment_service(
    repository: PaymentRepository = Depends(get_payment_repository),
) -> PaymentService:
    return PaymentService(repository)
