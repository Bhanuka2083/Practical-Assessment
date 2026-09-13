from collections.abc import Sequence
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.enums import OrderStatus
from app.models.order import Order, OrderItem
from app.repositories.base_repo import BaseRepository


class OrderRepository(BaseRepository):
    async def create_order(
        self,
        user_id: int,
        total_amount: Decimal,
        expires_at: datetime,
        status: OrderStatus = OrderStatus.RESERVED,
    ) -> Order:
        order = Order(
            user_id=user_id,
            status=status,
            total_amount=total_amount,
            expires_at=expires_at,
        )
        self.session.add(order)
        await self.session.flush()
        return order

    def add_order_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        unit_price: Decimal,
    ) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
        )
        self.session.add(item)
        return item

    async def get_by_id(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, order_id: int) -> Order | None:
        """Pessimistically locks the order for payment or status transitions."""
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_expired_reserved_orders(self, batch_size: int = 50) -> Sequence[Order]:
        """
        Pulls expired orders using SKIP LOCKED.
        Prevents background sweeper workers from blocking active checkouts.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(Order)
            .where(
                Order.status == OrderStatus.RESERVED,
                Order.expires_at <= now,
            )
            .options(
                selectinload(Order.items).selectinload(OrderItem.product)
            )
            .order_by(Order.id.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, order: Order, new_status: OrderStatus) -> None:
        order.status = new_status
        await self.session.flush()