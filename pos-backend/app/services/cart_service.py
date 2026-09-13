from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart import Cart, CartItem
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository

from app.core.database import atomic_transaction


class CartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.cart_repo = CartRepository(session)
        self.product_repo = ProductRepository(session)

    async def get_user_cart(self, user_id: int) -> Cart:
        return await self.cart_repo.get_or_create_active_cart(user_id)

    # app/services/cart_service.py in add_item_to_cart:

    async def add_item_to_cart(self, user_id: int, product_id: int, quantity: int) -> CartItem | None:
        product = await self.product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )

        cart = await self.cart_repo.get_or_create_active_cart(user_id)
        existing_item = await self.cart_repo.get_item(cart.id, product_id)
        current_qty = existing_item.quantity if existing_item else 0
        total_requested = current_qty + quantity

        # If item doesn't exist yet, initial quantity must be positive
        if not existing_item and quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than zero",
            )

        # Capacity check against available stock
        if total_requested > product.available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Insufficient stock for '{product.name}'. "
                    f"Requested: {total_requested}, Available: {product.available_stock}"
                ),
            )

        async with atomic_transaction(self.session):
            item = await self.cart_repo.add_or_update_item(cart.id, product_id, quantity)
        return item

    async def remove_item_from_cart(self, user_id: int, product_id: int) -> None:
        cart = await self.cart_repo.get_active_cart_by_user_id(user_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active cart not found")

        async with atomic_transaction(self.session):
            removed = await self.cart_repo.remove_item(cart.id, product_id)
            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Item does not exist in cart",
                )