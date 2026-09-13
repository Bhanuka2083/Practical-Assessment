from collections.abc import Sequence
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.repositories.base_repo import BaseRepository


class ProductRepository(BaseRepository):
    async def create(self, name: str, price: Decimal, total_stock: int) -> Product:
        product = Product(name=name, price=price, total_stock=total_stock, reserved_stock=0)
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[Product]:
        result = await self.session.execute(
            select(Product).order_by(Product.id.asc()).offset(skip).limit(limit)
        )
        return result.scalars().all()

    # app/repositories/product_repo.py

    async def get_products_for_update(self, product_ids: list[int]) -> Sequence[Product]:
        if not product_ids:
            return []

        sorted_ids = sorted(list(set(product_ids)))
        stmt = (
            select(Product)
            .where(Product.id.in_(sorted_ids))
            .order_by(Product.id.asc())
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def reserve_stock(self, product: Product, quantity: int) -> None:
        """Atomically increments reserved_stock in DB."""
        product.reserved_stock = Product.reserved_stock + quantity
        await self.session.flush()
        await self.session.refresh(product)

    async def release_reserved_stock(self, product: Product, quantity: int) -> None:
        """Atomically releases reserved_stock back to available inventory."""
        product.reserved_stock = Product.reserved_stock - quantity
        await self.session.flush()
        await self.session.refresh(product)

    async def commit_reserved_stock(self, product: Product, quantity: int) -> None:
        """Permanently settles stock on purchase."""
        product.total_stock = Product.total_stock - quantity
        product.reserved_stock = Product.reserved_stock - quantity
        await self.session.flush()
        await self.session.refresh(product)

    async def update(self, product: Product, **kwargs) -> Product:
        for field, value in kwargs.items():
            if value is not None and hasattr(product, field):
                setattr(product, field, value)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product: Product) -> None:
        await self.session.delete(product)
        await self.session.flush()