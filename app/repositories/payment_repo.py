from decimal import Decimal
from sqlalchemy import select

from app.models.enums import PaymentStatus
from app.models.payment import Payment
from app.repositories.base_repo import BaseRepository


class PaymentRepository(BaseRepository):
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_payment(
        self,
        order_id: int,
        idempotency_key: str,
        amount: Decimal,
        status: PaymentStatus = PaymentStatus.INITIATED,
    ) -> Payment:
        payment = Payment(
            order_id=order_id,
            idempotency_key=idempotency_key,
            amount=amount,
            status=status,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def update_payment_status(
        self,
        payment: Payment,
        status: PaymentStatus,
        gateway_reference: str | None = None,
    ) -> None:
        payment.status = status
        if gateway_reference:
            payment.gateway_reference = gateway_reference
        await self.session.flush()