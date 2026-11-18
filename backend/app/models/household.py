import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, GUID


class Household(Base):
    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    members = relationship(
        "HouseholdMember", back_populates="household", cascade="all, delete-orphan"
    )
    splits = relationship(
        "ExpenseSplit", back_populates="household", cascade="all, delete-orphan"
    )


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), default="MEMBER", nullable=False
    )  # OWNER, ADMIN, MEMBER
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    household = relationship("Household", back_populates="members")
    user = relationship("User")


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    household_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("receipts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    paid_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Shared expense"
    )
    split_type: Mapped[str] = mapped_column(
        String(50), default="EQUAL", nullable=False
    )  # EQUAL, PERCENTAGE, EXACT
    shares_data: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # JSON-encoded array of {user_id, share_amount}
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_settled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    household = relationship("Household", back_populates="splits")
    receipt = relationship("Receipt")
    payer = relationship("User", foreign_keys=[paid_by])
