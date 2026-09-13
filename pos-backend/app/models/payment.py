from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, CheckConstraint, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import PaymentStatus

if TYPE_CHECKING:
    from app.models.order import Order


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=True),
        default=PaymentStatus.INITIATED,
        nullable=False,
    )
    gateway_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payments")