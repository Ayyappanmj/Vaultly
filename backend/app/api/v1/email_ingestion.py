from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.common import MessageResponse
from app.services.ocr.parser import parse_receipt_text

router = APIRouter(prefix="/email-ingestion", tags=["Email Ingestion"])


class InboundEmailPayload(BaseModel):
    sender: EmailStr
    recipient: EmailStr
    subject: str
    body_text: str
    body_html: str | None = None
    attachments: list[dict[str, Any]] = []


class EmailIngestionProvider(ABC):
    @abstractmethod
    def parse_inbound_email(self, payload: InboundEmailPayload) -> dict[str, Any]:
        """Parses email payload into receipt attributes."""
        pass


class GenericEmailIngestionAdapter(EmailIngestionProvider):
    """Parses standard forwarded e-receipts and order confirmations."""

    def parse_inbound_email(self, payload: InboundEmailPayload) -> dict[str, Any]:
        text_content = payload.body_text
        parsed = parse_receipt_text(text_content)
        merchant = parsed.merchant_name or payload.subject[:50]
        return {
            "merchant_name": merchant,
            "purchase_date": parsed.purchase_date or datetime.now(timezone.utc),
            "total_amount": parsed.total_amount or Decimal("0.00"),
            "currency": parsed.currency or "USD",
            "receipt_number": parsed.receipt_number,
            "notes": f"Ingested from email subject: '{payload.subject}'",
            "ocr_raw_text": text_content,
        }


email_adapter = GenericEmailIngestionAdapter()


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def ingest_email(
    payload: InboundEmailPayload,
    db: Session = Depends(get_db),
    api_key: str | None = Header(default=None, alias="X-Email-Webhook-Secret"),
):
    """Inbound webhook endpoint for email delivery services (SendGrid Inbound Parse,
    Mailgun, Postmark, or AWS SES).
    Finds recipient user by recipient email address or routing alias.
    """
    # Map recipient (e.g. 'vault_user@vaultly.app' or user email)
    recipient_email = payload.recipient.lower()
    user = db.execute(
        select(User).where(User.email == recipient_email)
    ).scalar_one_or_none()

    if not user:
        # Check sender if forwarded from registered email
        sender_email = payload.sender.lower()
        user = db.execute(
            select(User).where(User.email == sender_email)
        ).scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered Vaultly user associated with inbound email sender or recipient.",
        )

    receipt_data = email_adapter.parse_inbound_email(payload)

    receipt = Receipt(
        user_id=user.id,
        merchant_name=receipt_data["merchant_name"],
        purchase_date=receipt_data["purchase_date"],
        total_amount=receipt_data["total_amount"],
        currency=receipt_data["currency"],
        receipt_number=receipt_data.get("receipt_number"),
        notes=receipt_data.get("notes"),
        ocr_raw_text=receipt_data.get("ocr_raw_text"),
        status="CONFIRMED" if receipt_data["total_amount"] > 0 else "REVIEW_NEEDED",
        sync_version=1,
    )
    db.add(receipt)
    db.commit()

    return MessageResponse(
        message=f"E-receipt from '{receipt.merchant_name}' ingested successfully."
    )
