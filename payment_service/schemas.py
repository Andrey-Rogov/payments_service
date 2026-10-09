from pydantic import BaseModel, ConfigDict, HttpUrl
from models import Currency, PaymentStatus
from datetime import datetime

class CreatePaymentRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: float
    currency: Currency
    description: str
    payment_metadata: dict | None
    webhook_url: HttpUrl | None = None


class CreatePaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: str
    status: PaymentStatus
    created_at: datetime | None = datetime.now()
