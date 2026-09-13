from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Price must be greater than zero")


class ProductCreate(ProductBase):
    total_stock: int = Field(..., ge=0, description="Initial total inventory count")


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    price: Decimal | None = Field(None, gt=0, decimal_places=2)
    total_stock: int | None = Field(None, ge=0)


class ProductResponse(ProductBase):
    id: int
    total_stock: int
    reserved_stock: int
    available_stock: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)