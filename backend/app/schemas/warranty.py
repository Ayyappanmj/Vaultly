import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class WarrantyBase(BaseModel):
    provider: str = Field(..., min_length=1, max_length=255)
    duration_months: int = Field(..., gt=0)
    start_date: datetime
    end_date: datetime | None = None  # Calculated automatically if omitted
    policy_number: str | None = None
    terms: str | None = None
    reminder_days: int = Field(default=30, ge=1)


class WarrantyCreate(WarrantyBase):
    purchase_id: uuid.UUID | None = None
    receipt_id: uuid.UUID | None = None


class WarrantyUpdate(BaseModel):
    provider: str | None = None
    duration_months: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    policy_number: str | None = None
    terms: str | None = None
    reminder_days: int | None = None
    status: str | None = None


class WarrantyResponse(WarrantyBase):
    id: uuid.UUID
    user_id: uuid.UUID
    purchase_id: uuid.UUID | None = None
    receipt_id: uuid.UUID | None = None
    end_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WarrantySuggestion(BaseModel):
    product_name: str
    suggested_duration_months: int
    provider: str
    reason: str
