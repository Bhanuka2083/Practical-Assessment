from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_active_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Retrieves current user's active draft cart with projected total."""
    service = CartService(db)
    return await service.get_user_cart(current_user.id)


@router.post("/items", response_model=CartResponse)
async def add_item_to_cart(
    payload: CartItemAdd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Adds line item to user's cart (tracks customer intent, zero stock hold)."""
    service = CartService(db)
    await service.add_item_to_cart(
        user_id=current_user.id,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )
    return await service.get_user_cart(current_user.id)


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = CartService(db)
    await service.remove_item_from_cart(user_id=current_user.id, product_id=product_id)