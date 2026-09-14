from datetime import datetime, timezone
from typing import Sequence
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderStatus
from app.models.order import OrderItem
from app.models.product import Product


class StockCleanerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def fetch_expired_reserved_orders(self, batch_size: int = 50) -> Sequence[Order]:
        """Locks and returns expired orders using SKIP LOCKED."""
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

    async def release_order_reservations(self, orders: Sequence[Order]) -> int:
        """
        Decrements reserved_stock for all items in the given orders
        and updates order status to EXPIRED or CANCELLED.
        """
        if not orders:
            return 0

        # 1. Aggregate stock reductions per product to minimize UPDATE queries
        stock_restorations: dict[int, int] = {}
        order_ids: list[int] = []

        for order in orders:
            order_ids.append(order.id)
            for item in order.items:
                stock_restorations[item.product_id] = (
                    stock_restorations.get(item.product_id, 0) + item.quantity
                )

        # 2. Atomically decrement reserved_stock on products
        for product_id, qty in stock_restorations.items():
            await self.session.execute(
                update(Product)
                .where(Product.id == product_id)
                .values(
                    reserved_stock=Product.reserved_stock - qty
                )
            )

        # 3. Mark orders as EXPIRED / CANCELLED
        await self.session.execute(
            update(Order)
            .where(Order.id.in_(order_ids))
            .values(status=OrderStatus.EXPIRED if hasattr(OrderStatus, "EXPIRED") else OrderStatus.CANCELLED)
        )

        return len(orders)