from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCancelResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders & Checkout"])


@router.post("/checkout", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def checkout_cart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Converts active cart to a RESERVED order.
    Pessimistically locks product rows in ASC order and places a 5-minute stock hold.
    """
    service = OrderService(db)
    return await service.checkout_cart(user_id=current_user.id)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = OrderRepository(db)
    order = await repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return order


@router.post("/{order_id}/cancel", response_model=OrderCancelResponse)
async def cancel_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancels a pending RESERVED order and immediately restores reserved stock."""
    service = OrderService(db)
    order = await service.cancel_order(user_id=current_user.id, order_id=order_id)
    return OrderCancelResponse(
        order_id=order.id,
        status=order.status,
        message="Order successfully cancelled and reserved inventory restored.",
    )