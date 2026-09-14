import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MockPaymentOutcome, OrderStatus, PaymentStatus
from app.models.payment import Payment
from app.repositories.order_repo import OrderRepository
from app.repositories.payment_repo import PaymentRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.payment import PaymentProcessResult, PaymentResponse

from app.core.database import atomic_transaction
from app.repositories import cart_repo


class PaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.order_repo = OrderRepository(session)
        self.product_repo = ProductRepository(session)
        self.cart_repo = cart_repo.CartRepository(session)

    async def process_payment(
        self,
        order_id: int,
        user_id: int,
        idempotency_key: str,
        outcome: MockPaymentOutcome,
    ) -> PaymentProcessResult:
        # Check for duplicate idempotency key
        existing_payment = await self.payment_repo.get_by_idempotency_key(idempotency_key)

        async with atomic_transaction(self.session):

            if existing_payment:
                order = await self.order_repo.get_by_id(order_id)
                order_status = order.status if order else "UNKNOWN"
                return PaymentProcessResult(
                    payment=PaymentResponse.model_validate(existing_payment),
                    order_status=order_status,
                    message="Duplicate request detected. Returning existing payment record.",
                )

            async with atomic_transaction(self.session):
                order = await self.order_repo.get_by_id_for_update(order_id)
                if not order:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

                if order.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

                # Check for order expiration (Lazy check)
                now = datetime.now(timezone.utc)
                if order.expires_at and order.expires_at <= now and order.status == OrderStatus.RESERVED:
                    # Release stock immediately
                    product_ids = sorted([i.product_id for i in order.items])
                    products = await self.product_repo.get_products_for_update(product_ids)
                    p_map = {p.id: p for p in products}
                    for item in order.items:
                        prod = p_map.get(item.product_id)
                        if prod:
                            await self.product_repo.release_reserved_stock(prod, item.quantity)

                    await self.order_repo.update_status(order, OrderStatus.EXPIRED)
                    raise HTTPException(
                        status_code=status.HTTP_410_GONE,
                        detail="Reservation has expired. Stock has been returned to inventory.",
                    )

                if order.status != OrderStatus.RESERVED:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Order cannot be paid. Current status: {order.status}",
                    )

                # Insert payment record with initial status
                try:
                    payment = await self.payment_repo.create_payment(
                        order_id=order.id,
                        idempotency_key=idempotency_key,
                        amount=order.total_amount,
                        status=PaymentStatus.INITIATED,
                    )
                except IntegrityError:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Payment with this idempotency key already exists or is in flight.",
                    )

                # Lock products involved in the order
                product_ids = sorted([item.product_id for item in order.items])
                products = await self.product_repo.get_products_for_update(product_ids)
                products_map = {p.id: p for p in products}

                # Process mock outcomes
                if outcome == MockPaymentOutcome.SUCCESS:
                    # Deduct both total and reserved stock permanently
                    for item in order.items:
                        prod = products_map.get(item.product_id)
                        if prod:
                            await self.product_repo.commit_reserved_stock(prod, item.quantity)

                    await self.order_repo.update_status(order, OrderStatus.PAID)
                    await self.payment_repo.update_payment_status(
                        payment,
                        status=PaymentStatus.SUCCESS,
                        gateway_reference=f"MOCK-TXN-{uuid.uuid4().hex[:12].upper()}",
                    )

                    cart = await self.cart_repo.get_active_cart_by_user_id(user_id)
                    if cart:
                        await self.cart_repo.clear_cart_items(cart.id)
                    message = "Payment successful. Stock permanently committed."

                elif outcome == MockPaymentOutcome.FAILURE:
                    # Release reserved stock back to available pool
                    for item in order.items:
                        prod = products_map.get(item.product_id)
                        if prod:
                            await self.product_repo.release_reserved_stock(prod, item.quantity)

                    await self.order_repo.update_status(order, OrderStatus.FAILED)
                    await self.payment_repo.update_payment_status(
                        payment,
                        status=PaymentStatus.FAILED,
                        gateway_reference=f"MOCK-FAIL-{uuid.uuid4().hex[:8].upper()}",
                    )
                    message = "Payment failed. Reserved stock released."

                elif outcome == MockPaymentOutcome.TIMEOUT:
                    # Gateway timeout: keep reservation active until manual retry or sweeper expiry
                    await self.payment_repo.update_payment_status(
                        payment,
                        status=PaymentStatus.TIMEOUT,
                    )
                    message = "Gateway timed out. Reservation remains active until expiry window ends."

            return PaymentProcessResult(
                payment=PaymentResponse.model_validate(payment),
                order_status=order.status,
                message=message,
            )