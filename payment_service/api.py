from typing import Any, Annotated
from fastapi import Depends, status, Header, Query
from fastapi import APIRouter, Path, Body
from logging import getLogger

from models import PaymentBase, PaymentStatus
from core.security import verify_api_key
from schemas import CreatePaymentRequest, CreatePaymentResponse
from service import PaymentService, get_payment_service

payments_router = APIRouter(prefix="/payments", tags=["payments v1"])
logger = getLogger("output")


@payments_router.post("/notify")
async def webhook_notification(
    _: Annotated[str, Depends(verify_api_key)],
    payment_id: Annotated[str, Query()],
    state: Annotated[PaymentStatus, Query()]
) -> Any:
    logger.info(f"Received webhook response: Payment ...{payment_id[-5:]} is now in status {state.value}")


@payments_router.get("/{payment_id}", response_model=PaymentBase)
async def get_payment(
    _: Annotated[..., Depends(verify_api_key)],
    service: Annotated[PaymentService, Depends(get_payment_service)],
    payment_id: Annotated[str, Path()]
) -> Any:
    return await service.get_payment(payment_id)


@payments_router.post("/", status_code=status.HTTP_202_ACCEPTED, response_model=CreatePaymentResponse)
async def create_payment(
    _: Annotated[..., Depends(verify_api_key)],
    service: Annotated[PaymentService, Depends(get_payment_service)],
    payload: Annotated[CreatePaymentRequest, Body()],
    idempotency_key: Annotated[str, Header(alias="X-Idempotency-Key")]
) -> Any:
    return await service.create_payment(payload, idempotency_key)
