from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import CartStatus
from app.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(..., description="Quantity delta (can be negative to decrement)")


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity must be at least 1")


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ProductResponse

    @property
    def line_total(self) -> Decimal:
        return Decimal(self.product.price) * self.quantity

    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    id: int
    user_id: int
    status: CartStatus
    items: list[CartItemResponse] = []

    @property
    def total_amount(self) -> Decimal:
        return sum((item.line_total for item in self.items), Decimal("0.00"))

    model_config = ConfigDict(from_attributes=True)