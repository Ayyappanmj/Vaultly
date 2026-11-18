import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class SubscriptionBase(BaseModel):
    service_name: str = Field(..., min_length=1, max_length=255)
    billing_frequency: str = Field(
        default="MONTHLY"
    )  # WEEKLY, MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY, CUSTOM
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    start_date: datetime
    next_renewal_date: datetime | None = None  # Calculated if omitted
    trial_end_date: datetime | None = None
    notes: str | None = None


class SubscriptionCreate(SubscriptionBase):
    status: str = Field(default="ACTIVE")


class SubscriptionUpdate(BaseModel):
    service_name: str | None = None
    billing_frequency: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    next_renewal_date: datetime | None = None
    trial_end_date: datetime | None = None
    cancellation_date: datetime | None = None
    notes: str | None = None


class SubscriptionResponse(SubscriptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    next_renewal_date: datetime
    cancellation_date: datetime | None = None
    monthly_equivalent: Decimal
    annual_equivalent: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionAnalytics(BaseModel):
    total_active_count: int
    total_monthly_spend: Decimal
    total_annual_spend: Decimal
    currency: str
    category_breakdown: dict[str, Decimal] = {}
    upcoming_renewals_next_30_days: list[SubscriptionResponse] = []
