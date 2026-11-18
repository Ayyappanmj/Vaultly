import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.purchase import Purchase
from app.models.receipt import Receipt
from app.models.subscription import Subscription
from app.models.user import User
from app.models.warranty import Warranty
from app.schemas.sync import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncOperation,
    SyncOperationResult,
)

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


@router.post("", response_model=SyncBatchResponse)
def process_sync_batch(
    batch: SyncBatchRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    results: list[SyncOperationResult] = []

    for op in batch.operations:
        try:
            if op.entity_type == "receipt":
                res = _sync_receipt(db, current_user.id, op)
            elif op.entity_type == "purchase":
                res = _sync_purchase(db, current_user.id, op)
            elif op.entity_type == "warranty":
                res = _sync_warranty(db, current_user.id, op)
            elif op.entity_type == "subscription":
                res = _sync_subscription(db, current_user.id, op)
            else:
                res = SyncOperationResult(
                    operation_id=op.operation_id,
                    status="FAILED",
                    entity_id=op.entity_id,
                    error_message=f"Unknown entity type {op.entity_type}",
                )
            results.append(res)
        except Exception as exc:
            results.append(
                SyncOperationResult(
                    operation_id=op.operation_id,
                    status="FAILED",
                    entity_id=op.entity_id,
                    error_message=str(exc),
                )
            )

    db.commit()
    return SyncBatchResponse(processed_count=len(results), results=results)


def _sync_receipt(
    db: Session, user_id: uuid.UUID, op: SyncOperation
) -> SyncOperationResult:
    existing = db.execute(
        select(Receipt).where(Receipt.id == op.entity_id, Receipt.user_id == user_id)
    ).scalar_one_or_none()

    if op.action == "CREATE":
        if existing:
            # Idempotency guarantee: already created, do not duplicate!
            return SyncOperationResult(
                operation_id=op.operation_id,
                status="SYNCED",
                server_version=existing.sync_version,
                entity_id=existing.id,
            )

        p = op.payload
        dt = (
            datetime.fromisoformat(p.get("purchase_date"))
            if p.get("purchase_date")
            else datetime.now(timezone.utc)
        )
        receipt = Receipt(
            id=op.entity_id,
            user_id=user_id,
            merchant_name=p.get("merchant_name", "Untitled Receipt"),
            purchase_date=dt,
            total_amount=Decimal(str(p.get("total_amount", "0.00"))),
            currency=p.get("currency", "USD"),
            status=p.get("status", "CONFIRMED"),
            receipt_number=p.get("receipt_number"),
            notes=p.get("notes"),
            sync_version=1,
        )
        db.add(receipt)
        return SyncOperationResult(
            operation_id=op.operation_id,
            status="SYNCED",
            server_version=1,
            entity_id=op.entity_id,
        )

    if op.action == "UPDATE":
        if not existing:
            return SyncOperationResult(
                operation_id=op.operation_id,
                status="FAILED",
                entity_id=op.entity_id,
                error_message="Entity not found on server",
            )

        # Conflict detection via version numbering
        if existing.sync_version > op.client_version:
            return SyncOperationResult(
                operation_id=op.operation_id,
                status="CONFLICT",
                server_version=existing.sync_version,
                entity_id=existing.id,
                error_message="Server has a newer version of this receipt.",
                server_data={
                    "merchant_name": existing.merchant_name,
                    "total_amount": str(existing.total_amount),
                    "purchase_date": existing.purchase_date.isoformat(),
                    "sync_version": existing.sync_version,
                },
            )

        p = op.payload
        if "merchant_name" in p:
            existing.merchant_name = p["merchant_name"]
        if "total_amount" in p:
            existing.total_amount = Decimal(str(p["total_amount"]))
        if "notes" in p:
            existing.notes = p["notes"]
        existing.sync_version += 1

        return SyncOperationResult(
            operation_id=op.operation_id,
            status="SYNCED",
            server_version=existing.sync_version,
            entity_id=existing.id,
        )

    if op.action == "DELETE":
        if existing:
            existing.is_deleted = True
            existing.sync_version += 1
        return SyncOperationResult(
            operation_id=op.operation_id,
            status="SYNCED",
            server_version=existing.sync_version if existing else 1,
            entity_id=op.entity_id,
        )

    return SyncOperationResult(
        operation_id=op.operation_id, status="FAILED", entity_id=op.entity_id
    )


def _sync_purchase(
    db: Session, user_id: uuid.UUID, op: SyncOperation
) -> SyncOperationResult:
    existing = db.execute(
        select(Purchase).where(Purchase.id == op.entity_id, Purchase.user_id == user_id)
    ).scalar_one_or_none()

    if op.action == "CREATE":
        if existing:
            return SyncOperationResult(
                operation_id=op.operation_id, status="SYNCED", entity_id=existing.id
            )
        p = op.payload
        dt = (
            datetime.fromisoformat(p.get("purchase_date"))
            if p.get("purchase_date")
            else datetime.now(timezone.utc)
        )
        purchase = Purchase(
            id=op.entity_id,
            user_id=user_id,
            product_name=p.get("product_name", "Untitled Product"),
            brand=p.get("brand"),
            purchase_date=dt,
            price=Decimal(str(p.get("price", "0.00"))) if p.get("price") else None,
            currency=p.get("currency", "USD"),
        )
        db.add(purchase)
        return SyncOperationResult(
            operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
        )

    if op.action == "DELETE" and existing:
        db.delete(existing)
        return SyncOperationResult(
            operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
        )

    return SyncOperationResult(
        operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
    )


def _sync_warranty(
    db: Session, user_id: uuid.UUID, op: SyncOperation
) -> SyncOperationResult:
    existing = db.execute(
        select(Warranty).where(Warranty.id == op.entity_id, Warranty.user_id == user_id)
    ).scalar_one_or_none()

    if op.action == "CREATE":
        if existing:
            return SyncOperationResult(
                operation_id=op.operation_id, status="SYNCED", entity_id=existing.id
            )
        p = op.payload
        start_d = datetime.fromisoformat(p["start_date"])
        end_d = datetime.fromisoformat(p["end_date"])
        warranty = Warranty(
            id=op.entity_id,
            user_id=user_id,
            provider=p.get("provider", "Manufacturer"),
            duration_months=int(p.get("duration_months", 12)),
            start_date=start_d,
            end_date=end_d,
            status="ACTIVE",
        )
        db.add(warranty)
        return SyncOperationResult(
            operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
        )

    return SyncOperationResult(
        operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
    )


def _sync_subscription(
    db: Session, user_id: uuid.UUID, op: SyncOperation
) -> SyncOperationResult:
    existing = db.execute(
        select(Subscription).where(
            Subscription.id == op.entity_id, Subscription.user_id == user_id
        )
    ).scalar_one_or_none()

    if op.action == "CREATE":
        if existing:
            return SyncOperationResult(
                operation_id=op.operation_id, status="SYNCED", entity_id=existing.id
            )
        p = op.payload
        start_d = datetime.fromisoformat(p["start_date"])
        renew_d = datetime.fromisoformat(p["next_renewal_date"])
        sub = Subscription(
            id=op.entity_id,
            user_id=user_id,
            service_name=p.get("service_name", "Service"),
            billing_frequency=p.get("billing_frequency", "MONTHLY"),
            amount=Decimal(str(p.get("amount", "0.00"))),
            currency=p.get("currency", "USD"),
            status=p.get("status", "ACTIVE"),
            start_date=start_d,
            next_renewal_date=renew_d,
        )
        db.add(sub)
        return SyncOperationResult(
            operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
        )

    return SyncOperationResult(
        operation_id=op.operation_id, status="SYNCED", entity_id=op.entity_id
    )
