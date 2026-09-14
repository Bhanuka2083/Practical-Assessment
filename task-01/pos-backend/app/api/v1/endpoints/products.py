from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.core.security import require_admin
from app.repositories.product_repo import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(prefix="/products", tags=["Products & Inventory"])


@router.get("", response_model=list[ProductResponse])
@router.get("/", response_model=list[ProductResponse], include_in_schema=False)
async def list_products(db: Annotated[AsyncSession, Depends(get_db)]):
    repo = ProductRepository(db)
    return await repo.get_all()


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


# app/api/v1/endpoints/products.py

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = ProductRepository(db)
    product = await repo.create(
        name=payload.name,
        price=payload.price,
        total_stock=payload.total_stock,
    )
    await db.commit()
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    try:
        updated = await repo.update(
            product,
            name=payload.name,
            price=payload.price,
            total_stock=payload.total_stock,
        )
        await db.commit()
        return updated
    except ValueError as err:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    current_admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await repo.delete(product)
    await db.commit()