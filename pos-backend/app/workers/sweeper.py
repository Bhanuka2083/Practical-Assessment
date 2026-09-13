import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.enums import OrderStatus
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository

logger = logging.getLogger("pos.sweeper")


class ReservationSweeper:
    def __init__(self) -> None:
        self._is_running = False
        self._task: asyncio.Task | None = None

    async def sweep_expired_reservations(self) -> int:
        """
        Pulls expired reserved orders and restores reserved stock.
        Returns the number of expired orders reclaimed in this run.
        """
        async with AsyncSessionLocal() as session:
            order_repo = OrderRepository(session)
            product_repo = ProductRepository(session)

            async with session.begin():
                # 1. Fetch expired orders with SKIP LOCKED (non-blocking)
                expired_orders = await order_repo.get_expired_reserved_orders(batch_size=50)
                if not expired_orders:
                    return 0

                # 2. Extract and sort all unique product IDs across expired orders
                product_ids: set[int] = set()
                for order in expired_orders:
                    for item in order.items:
                        product_ids.add(item.product_id)

                sorted_product_ids = sorted(list(product_ids))

                # 3. Lock products deterministically (ORDER BY id ASC FOR UPDATE)
                locked_products = await product_repo.get_products_for_update(sorted_product_ids)
                product_map = {p.id: p for p in locked_products}

                # 4. Release held stock back to available pool
                for order in expired_orders:
                    for item in order.items:
                        product = product_map.get(item.product_id)
                        if product:
                            await product_repo.release_reserved_stock(product, item.quantity)

                    # 5. Transition order to terminal EXPIRED status
                    await order_repo.update_status(order, OrderStatus.EXPIRED)

                logger.info(
                    "Reclaimed %d expired orders and restored their reserved inventory.",
                    len(expired_orders),
                )
                return len(expired_orders)

    async def _run_loop(self, interval_seconds: int = 15) -> None:
        """Periodic background polling loop."""
        logger.info("Stock reservation sweeper started (interval: %ds).", interval_seconds)
        while self._is_running:
            try:
                await self.sweep_expired_reservations()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Error running reservation sweeper: %s", exc, exc_info=True)

            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break

        logger.info("Stock reservation sweeper stopped.")

    def start(self, interval_seconds: int = 15) -> None:
        if not self._is_running:
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop(interval_seconds))

    async def stop(self) -> None:
        if self._is_running:
            self._is_running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass


# Singleton instance
sweeper = ReservationSweeper()