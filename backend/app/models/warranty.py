import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class Warranty(Base):
    __tablename__ = "warranties"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    purchase_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("purchases.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("receipts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    policy_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE", index=True, nullable=False
    )
    reminder_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="warranties")
    purchase = relationship("Purchase", back_populates="warranties")
    receipt = relationship("Receipt", back_populates="warranties")
