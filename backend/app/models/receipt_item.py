import uuid
from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=1, nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    receipt = relationship("Receipt", back_populates="items")
