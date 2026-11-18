import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, GUID


class OCRJob(Base):
    __tablename__ = "ocr_jobs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("receipts.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="PENDING", index=True, nullable=False
    )  # PENDING, PROCESSING, COMPLETED, FAILED
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded
    confidence_scores: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON-encoded
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
