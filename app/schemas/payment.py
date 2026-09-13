from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import MockPaymentOutcome, PaymentStatus


class PaymentRequest(BaseModel):
    simulate_outcome: MockPaymentOutcome = Field(
        default=MockPaymentOutcome.SUCCESS,
        description="Simulate outcome: SUCCESS, FAILURE, or TIMEOUT"
    )


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    idempotency_key: str
    amount: Decimal
    status: PaymentStatus
    gateway_reference: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentProcessResult(BaseModel):
    payment: PaymentResponse
    order_status: str
    message: str