import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.stock_cleaner_repo import StockCleanerRepository

logger = logging.getLogger(__name__)


class StockCleanerService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = StockCleanerRepository(session)

    async def sweep_expired_reservations(self, batch_size: int = 50) -> dict:
        """Sweeps all expired reservations in batches and commits changes."""
        total_cleaned = 0

        while True:
            # 1. Lock a batch of expired orders
            orders = await self.repo.fetch_expired_reserved_orders(batch_size=batch_size)
            if not orders:
                break

            # 2. Release product reservations and flip status
            cleaned_count = await self.repo.release_order_reservations(orders)
            await self.session.commit()
            
            total_cleaned += cleaned_count
            logger.info("Released stock for %d expired orders.", cleaned_count)

        return {"cleaned_orders_count": total_cleaned}