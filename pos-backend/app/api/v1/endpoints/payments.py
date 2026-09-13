from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.payment import PaymentProcessResult, PaymentRequest
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/orders", tags=["Payments"])


@router.post("/{order_id}/pay", response_model=PaymentProcessResult)
async def pay_order(
    order_id: int,
    payload: PaymentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[
        str | None,
        Header(alias="Idempotency-Key", description="Unique UUID to prevent duplicate charges"),
    ] = None,
):
    """
    Submits payment for an order.
    Requires an Idempotency-Key header to reject duplicate or concurrent attempts.
    """
    if not idempotency_key or not idempotency_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'Idempotency-Key' HTTP header",
        )

    service = PaymentService(db)
    return await service.process_payment(
        order_id=order_id,
        user_id=current_user.id,
        idempotency_key=idempotency_key.strip(),
        outcome=payload.simulate_outcome,
    )