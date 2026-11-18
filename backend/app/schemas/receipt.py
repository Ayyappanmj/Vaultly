import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryResponse


class ReceiptItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(default=Decimal("1.0"))
    unit_price: Decimal | None = None
    total_price: Decimal


class ReceiptItemCreate(ReceiptItemBase):
    category_id: uuid.UUID | None = None


class ReceiptItemResponse(ReceiptItemBase):
    id: uuid.UUID
    receipt_id: uuid.UUID
    category_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class ReceiptImageResponse(BaseModel):
    id: uuid.UUID
    file_path: str
    file_size: int
    mime_type: str
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceiptBase(BaseModel):
    merchant_name: str = Field(..., min_length=1, max_length=255)
    purchase_date: datetime
    total_amount: Decimal
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: str | None = None
    receipt_number: str | None = None
    notes: str | None = None
    status: str = Field(default="CONFIRMED")


class ReceiptCreate(ReceiptBase):
    category_id: uuid.UUID | None = None
    items: list[ReceiptItemCreate] = []


class ReceiptUpdate(BaseModel):
    merchant_name: str | None = None
    purchase_date: datetime | None = None
    total_amount: Decimal | None = None
    subtotal: Decimal | None = None
    tax_amount: Decimal | None = None
    currency: str | None = None
    payment_method: str | None = None
    receipt_number: str | None = None
    notes: str | None = None
    category_id: uuid.UUID | None = None
    status: str | None = None


class ReceiptResponse(ReceiptBase):
    id: uuid.UUID
    user_id: uuid.UUID
    category_id: uuid.UUID | None = None
    category: CategoryResponse | None = None
    is_deleted: bool
    sync_version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReceiptDetailResponse(ReceiptResponse):
    items: list[ReceiptItemResponse] = []
    images: list[ReceiptImageResponse] = []
