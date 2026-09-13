from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.enums import CartStatus, OrderStatus
from app.models.order import Order
from app.repositories.cart_repo import CartRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository

from app.core.database import atomic_transaction


class OrderService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.order_repo = OrderRepository(session)
        self.product_repo = ProductRepository(session)
        self.cart_repo = CartRepository(session)

    # app/services/order_service.py

    async def checkout_cart(self, user_id: int) -> Order:
        cart = await self.cart_repo.get_active_cart_by_user_id(user_id)
        if not cart or not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty or not found",
            )

        cart_items_map = {item.product_id: item.quantity for item in cart.items}
        product_ids = sorted(list(cart_items_map.keys()))

        # Safe transaction entry
        # txn = self.session.begin_nested() if self.session.in_transaction() else self.session.begin()
        # async with txn:
        async with atomic_transaction(self.session):
            products = await self.product_repo.get_products_for_update(product_ids)

            if len(products) != len(product_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="One or more products in your cart no longer exist",
                )

            total_amount = Decimal("0.00")
            for product in products:
                requested_qty = cart_items_map[product.id]
                
                # Check fresh locked stock
                if product.available_stock < requested_qty:
                    # ✅ Do NOT call session.rollback() here!
                    # Raising HTTPException causes atomic_transaction to auto-rollback
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            f"Stock conflict for '{product.name}'. "
                            f"Available: {product.available_stock}, Requested: {requested_qty}"
                        ),
                    )
                total_amount += Decimal(product.price) * requested_qty

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=settings.RESERVATION_EXPIRY_MINUTES)
            order = await self.order_repo.create_order(
                user_id=user_id,
                total_amount=total_amount,
                expires_at=expires_at,
                status=OrderStatus.RESERVED,
            )

            for product in products:
                requested_qty = cart_items_map[product.id]
                await self.product_repo.reserve_stock(product, requested_qty)
                self.order_repo.add_order_item(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=requested_qty,
                    unit_price=Decimal(product.price),
                )

            await self.cart_repo.clear_cart_items(cart.id)
            cart.status = CartStatus.ACTIVE

        # Ensure changes are fully committed to database
        await self.session.commit()

        refreshed_order = await self.order_repo.get_by_id(order.id)
        if not refreshed_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created order",
            )
        return refreshed_order

    async def cancel_order(self, user_id: int, order_id: int) -> Order:
        """
        Manually cancels an active RESERVED order and restores reserved inventory.
        """
        async with atomic_transaction(self.session):
            order = await self.order_repo.get_by_id_for_update(order_id)
            if not order:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

            if order.user_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this order")

            if order.status != OrderStatus.RESERVED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot cancel order with status '{order.status}'",
                )

            # Lock products involved in this order
            product_ids = sorted([item.product_id for item in order.items])
            products = await self.product_repo.get_products_for_update(product_ids)
            products_map = {p.id: p for p in products}

            # Return reserved inventory to available stock
            for item in order.items:
                prod = products_map.get(item.product_id)
                if prod:
                    await self.product_repo.release_reserved_stock(prod, item.quantity)

            await self.order_repo.update_status(order, OrderStatus.CANCELLED)

        return order