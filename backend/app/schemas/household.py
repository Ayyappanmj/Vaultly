import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class HouseholdCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class HouseholdMemberResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: str
    joined_at: datetime
    email: str | None = None
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HouseholdResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_by: uuid.UUID
    created_at: datetime
    members: list[HouseholdMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ShareItem(BaseModel):
    user_id: uuid.UUID
    percentage: Decimal | None = None
    exact_amount: Decimal | None = None


class ExpenseSplitCreate(BaseModel):
    receipt_id: uuid.UUID | None = None
    description: str = Field(default="Shared expense")
    split_type: str = Field(default="EQUAL", pattern="^(EQUAL|PERCENTAGE|EXACT)$")
    total_amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    shares: list[ShareItem] = []  # For PERCENTAGE or EXACT splits


class ShareResult(BaseModel):
    user_id: uuid.UUID
    user_name: str | None = None
    share_amount: Decimal


class ExpenseSplitResponse(BaseModel):
    id: uuid.UUID
    household_id: uuid.UUID
    receipt_id: uuid.UUID | None = None
    paid_by: uuid.UUID
    payer_name: str | None = None
    description: str
    split_type: str
    total_amount: Decimal
    currency: str
    is_settled: bool
    shares: list[ShareResult] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemberBalance(BaseModel):
    user_id: uuid.UUID
    full_name: str
    total_paid: Decimal
    total_owed: Decimal
    net_balance: Decimal  # Positive = owed money, Negative = owes money


class HouseholdBalanceReport(BaseModel):
    household_id: uuid.UUID
    currency: str
    member_balances: list[MemberBalance] = []
