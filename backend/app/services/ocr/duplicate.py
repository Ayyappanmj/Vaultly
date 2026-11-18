import hashlib
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.receipt import Receipt
from app.models.receipt_image import ReceiptImage


def check_for_duplicate_receipt(
    db: Session,
    user_id: uuid.UUID,
    merchant_name: str | None,
    purchase_date: datetime | None,
    total_amount: Decimal | None,
    receipt_number: str | None = None,
    ocr_raw_text: str | None = None,
    perceptual_hash: str | None = None,
) -> tuple[bool, str | None]:
    """Checks for existing potential duplicates using multiple heuristic signals:
    1. Exact receipt number for same user
    2. Same merchant + same date (within 1 day) + same total amount
    3. Identical OCR text hash
    4. Identical perceptual image hash

    Returns (is_duplicate: bool, warning_message: str | None).
    Never auto-deletes; produces an advisory warning.
    """
    # 1. Receipt number match
    if receipt_number:
        existing = db.execute(
            select(Receipt).where(
                Receipt.user_id == user_id,
                Receipt.receipt_number == receipt_number,
                Receipt.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing:
            return (
                True,
                f"Possible duplicate: A receipt with number '{receipt_number}' already exists.",
            )

    # 2. Merchant + Date + Total match
    if merchant_name and purchase_date and total_amount:
        start_range = purchase_date - timedelta(days=1)
        end_range = purchase_date + timedelta(days=1)

        stmt = select(Receipt).where(
            Receipt.user_id == user_id,
            Receipt.merchant_name.ilike(merchant_name.strip()),
            Receipt.total_amount == total_amount,
            Receipt.purchase_date >= start_range,
            Receipt.purchase_date <= end_range,
            Receipt.is_deleted.is_(False),
        )
        existing = db.execute(stmt).scalar_one_or_none()
        if existing:
            return (
                True,
                f"Possible duplicate: Found identical amount ${total_amount} at '{merchant_name}' on {purchase_date.strftime('%Y-%m-%d')}.",
            )

    # 3. Raw text SHA-256 hash match
    if ocr_raw_text and len(ocr_raw_text.strip()) > 50:
        clean_text = "".join(ocr_raw_text.split()).lower()
        text_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

        # Check existing receipts with matching text hash if stored or query
        existing = (
            db.execute(
                select(Receipt).where(
                    Receipt.user_id == user_id,
                    Receipt.ocr_raw_text.isnot(None),
                    Receipt.is_deleted.is_(False),
                )
            )
            .scalars()
            .all()
        )
        for r in existing:
            if r.ocr_raw_text:
                candidate_hash = hashlib.sha256(
                    "".join(r.ocr_raw_text.split()).lower().encode("utf-8")
                ).hexdigest()
                if candidate_hash == text_hash:
                    return (
                        True,
                        "Possible duplicate: Exact OCR text match with an existing receipt.",
                    )

    # 4. Perceptual image hash match
    if perceptual_hash and perceptual_hash != "0000000000000000":
        existing_img = db.execute(
            select(ReceiptImage)
            .join(Receipt)
            .where(
                Receipt.user_id == user_id,
                ReceiptImage.perceptual_hash == perceptual_hash,
                Receipt.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing_img:
            return (
                True,
                "Possible duplicate: Image visual fingerprint matches an existing receipt image.",
            )

    return False, None
