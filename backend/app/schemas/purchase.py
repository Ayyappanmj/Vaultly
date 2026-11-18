import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PurchaseBase(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=255)
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    purchase_date: datetime
    price: Decimal | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    notes: str | None = None


class PurchaseCreate(PurchaseBase):
    receipt_id: uuid.UUID | None = None


class PurchaseUpdate(BaseModel):
    product_name: str | None = None
    brand: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    purchase_date: datetime | None = None
    price: Decimal | None = None
    currency: str | None = None
    notes: str | None = None
    receipt_id: uuid.UUID | None = None


class PurchaseResponse(PurchaseBase):
    id: uuid.UUID
    user_id: uuid.UUID
    receipt_id: uuid.UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
