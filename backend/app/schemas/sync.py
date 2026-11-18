import uuid
from typing import Any
from pydantic import BaseModel, Field


class SyncOperation(BaseModel):
    operation_id: str
    entity_type: str = Field(..., pattern="^(receipt|purchase|warranty|subscription)$")
    action: str = Field(..., pattern="^(CREATE|UPDATE|DELETE)$")
    entity_id: uuid.UUID
    client_version: int = 1
    timestamp: str
    payload: dict[str, Any] = {}


class SyncBatchRequest(BaseModel):
    client_id: str
    operations: list[SyncOperation] = []


class SyncOperationResult(BaseModel):
    operation_id: str
    status: str  # SYNCED, CONFLICT, FAILED, IGNORED
    server_version: int = 1
    entity_id: uuid.UUID
    error_message: str | None = None
    server_data: dict[str, Any] | None = None


class SyncBatchResponse(BaseModel):
    processed_count: int
    results: list[SyncOperationResult] = []
