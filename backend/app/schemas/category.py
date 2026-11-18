import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = Field(default="tag", max_length=50)
    color: str = Field(default="#6366f1", max_length=20)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
