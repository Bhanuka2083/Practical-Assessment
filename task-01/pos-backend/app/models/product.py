from decimal import Decimal
from sqlalchemy import BigInteger, CheckConstraint, Numeric, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("total_stock >= 0", name="chk_stock_non_negative"),
        CheckConstraint("reserved_stock >= 0 AND reserved_stock <= total_stock", name="chk_reserved_bounds"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_stock: Mapped[int] = mapped_column(default=0, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(default=0, nullable=False)

    @hybrid_property
    def available_stock(self) -> int:
        """Dynamically calculated unreserved stock ready for purchase."""
        return self.total_stock - self.reserved_stock