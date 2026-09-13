from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.models.enums import CartStatus
from app.repositories.base_repo import BaseRepository


class CartRepository(BaseRepository):
    async def get_active_cart_by_user_id(self, user_id: int) -> Cart | None:
        """Retrieves user's active cart with preloaded items and products."""
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id, Cart.status == CartStatus.ACTIVE)
            .options(
                selectinload(Cart.items).selectinload(CartItem.product)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_active_cart(self, user_id: int) -> Cart:
        cart = await self.get_active_cart_by_user_id(user_id)
        if not cart:
            cart = Cart(user_id=user_id, status=CartStatus.ACTIVE)
            self.session.add(cart)
            await self.session.flush()
            await self.session.refresh(cart, attribute_names=["items"])
        return cart

    async def get_item(self, cart_id: int, product_id: int) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_or_update_item(self, cart_id: int, product_id: int, quantity: int) -> CartItem:
        item = await self.get_item(cart_id, product_id)
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
            self.session.add(item)
        await self.session.flush()
        return item

    async def remove_item(self, cart_id: int, product_id: int) -> bool:
        stmt = delete(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def clear_cart_items(self, cart_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )