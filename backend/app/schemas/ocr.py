import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class ParsedLineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal("1.0")
    unit_price: Decimal | None = None
    total_price: Decimal
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class ParsedReceiptData(BaseModel):
    merchant_name: str | None = None
    merchant_confidence: float = 0.0
    purchase_date: datetime | None = None
    date_confidence: float = 0.0
    receipt_number: str | None = None
    receipt_number_confidence: float = 0.0
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    total_confidence: float = 0.0
    currency: str = "USD"
    payment_method: str | None = None
    line_items: list[ParsedLineItem] = []
    overall_confidence: float = 0.0
    is_duplicate: bool = False
    duplicate_warning: str | None = None


class OCRJobResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    receipt_id: uuid.UUID | None = None
    status: str
    raw_text: str | None = None
    parsed_data: ParsedReceiptData | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OCRReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(CONFIRM|EDIT|RETRY|CANCEL)$")
    merchant_name: str | None = None
    purchase_date: datetime | None = None
    total_amount: Decimal | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    currency: str | None = None
    category_id: uuid.UUID | None = None
    notes: str | None = None
    line_items: list[ParsedLineItem] | None = None
