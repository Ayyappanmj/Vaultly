import json
import uuid
from datetime import datetime
from decimal import Decimal
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, handle_idempotent_request
from app.core.database import get_db
from app.models.receipt import Receipt
from app.models.receipt_image import ReceiptImage
from app.models.receipt_item import ReceiptItem
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.receipt import (
    ReceiptCreate,
    ReceiptDetailResponse,
    ReceiptImageResponse,
    ReceiptResponse,
    ReceiptUpdate,
)
from app.services.ocr.duplicate import check_for_duplicate_receipt
from app.services.ocr.preprocessor import compute_perceptual_hash
from app.storage.service import storage_service

router = APIRouter(prefix="/receipts", tags=["Receipts"])


@router.get("", response_model=PaginatedResponse[ReceiptResponse])
def list_receipts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category_id: uuid.UUID | None = None,
    merchant: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_amount: Decimal | None = None,
    max_amount: Decimal | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Receipt)
        .options(joinedload(Receipt.category))
        .where(Receipt.user_id == current_user.id, Receipt.is_deleted.is_(False))
    )

    if category_id:
        stmt = stmt.where(Receipt.category_id == category_id)
    if merchant:
        stmt = stmt.where(Receipt.merchant_name.ilike(f"%{merchant.strip()}%"))
    if start_date:
        stmt = stmt.where(Receipt.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(Receipt.purchase_date <= end_date)
    if min_amount is not None:
        stmt = stmt.where(Receipt.total_amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Receipt.total_amount <= max_amount)

    # Count total items
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    # Paginate and order by newest first
    stmt = stmt.order_by(Receipt.purchase_date.desc(), Receipt.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    items = db.execute(stmt).scalars().all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaginatedResponse[ReceiptResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "", response_model=ReceiptDetailResponse, status_code=status.HTTP_201_CREATED
)
def create_receipt(
    body: ReceiptCreate,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Idempotency check
    record, cached = handle_idempotent_request(
        db,
        current_user.id,
        "/api/v1/receipts",
        idempotency_key,
        body.model_dump(mode="json"),
    )
    if cached:
        return cached

    # Check for potential duplicates
    is_dup, warning = check_for_duplicate_receipt(
        db=db,
        user_id=current_user.id,
        merchant_name=body.merchant_name,
        purchase_date=body.purchase_date,
        total_amount=body.total_amount,
        receipt_number=body.receipt_number,
    )

    receipt_status = "DUPLICATE_WARNING" if is_dup else (body.status or "CONFIRMED")
    notes = body.notes or ""
    if warning:
        notes = f"[{warning}] {notes}".strip()

    receipt = Receipt(
        user_id=current_user.id,
        category_id=body.category_id,
        merchant_name=body.merchant_name,
        purchase_date=body.purchase_date,
        total_amount=body.total_amount,
        subtotal=body.subtotal,
        tax_amount=body.tax_amount,
        currency=body.currency.upper(),
        payment_method=body.payment_method,
        receipt_number=body.receipt_number,
        notes=notes,
        status=receipt_status,
        sync_version=1,
    )
    db.add(receipt)
    db.flush()

    for item_data in body.items:
        item = ReceiptItem(
            receipt_id=receipt.id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price,
            category_id=item_data.category_id or body.category_id,
        )
        db.add(item)

    db.commit()

    # Load complete receipt with items and category
    full_receipt = (
        db.execute(
            select(Receipt)
            .options(
                joinedload(Receipt.items),
                joinedload(Receipt.images),
                joinedload(Receipt.category),
            )
            .where(Receipt.id == receipt.id)
        )
        .unique()
        .scalar_one()
    )

    resp_data = ReceiptDetailResponse.model_validate(full_receipt).model_dump(
        mode="json"
    )

    # If idempotency record was requested, save response
    if record:
        record.response_body = json.dumps(resp_data, default=str)
        db.add(record)
        db.commit()

    return resp_data


@router.get("/{receipt_id}", response_model=ReceiptDetailResponse)
def get_receipt(
    receipt_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Receipt)
        .options(
            joinedload(Receipt.items),
            joinedload(Receipt.images),
            joinedload(Receipt.category),
        )
        .where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
            Receipt.is_deleted.is_(False),
        )
    )
    receipt = db.execute(stmt).unique().scalar_one_or_none()
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )
    return receipt


@router.put("/{receipt_id}", response_model=ReceiptDetailResponse)
def update_receipt(
    receipt_id: uuid.UUID,
    body: ReceiptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    receipt = db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
            Receipt.is_deleted.is_(False),
        )
    ).scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(receipt, field, val)

    receipt.sync_version += 1
    db.commit()

    full_receipt = (
        db.execute(
            select(Receipt)
            .options(
                joinedload(Receipt.items),
                joinedload(Receipt.images),
                joinedload(Receipt.category),
            )
            .where(Receipt.id == receipt.id)
        )
        .unique()
        .scalar_one()
    )
    return full_receipt


@router.delete("/{receipt_id}", response_model=MessageResponse)
def delete_receipt(
    receipt_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    receipt = db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
            Receipt.is_deleted.is_(False),
        )
    ).scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )

    # Soft delete
    receipt.is_deleted = True
    receipt.sync_version += 1
    db.commit()
    return MessageResponse(message="Receipt deleted successfully.")


@router.post("/{receipt_id}/images", response_model=ReceiptImageResponse)
async def upload_receipt_image(
    receipt_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify user owns receipt
    receipt = db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
            Receipt.is_deleted.is_(False),
        )
    ).scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )

    content = await file.read()
    mime_type = storage_service.validate_file(file, content)

    rel_path, file_hash, size = storage_service.save_file(
        content, file.filename or "receipt.jpg", current_user.id
    )

    # Compute perceptual hash if image
    full_path = str(storage_service.base_dir / rel_path)
    p_hash = compute_perceptual_hash(full_path) if "image" in mime_type else None

    image_entity = ReceiptImage(
        receipt_id=receipt.id,
        file_path=rel_path,
        file_size=size,
        mime_type=mime_type,
        file_hash=file_hash,
        perceptual_hash=p_hash,
        is_primary=True,
    )
    db.add(image_entity)
    receipt.sync_version += 1
    db.commit()
    db.refresh(image_entity)
    return image_entity


@router.get("/{receipt_id}/images/{image_id}/download")
def download_receipt_image(
    receipt_id: uuid.UUID,
    image_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Strictly authenticated endpoint with user isolation
    receipt = db.execute(
        select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == current_user.id,
            Receipt.is_deleted.is_(False),
        )
    ).scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )

    image = db.execute(
        select(ReceiptImage).where(
            ReceiptImage.id == image_id,
            ReceiptImage.receipt_id == receipt.id,
        )
    ).scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found."
        )

    file_bytes = storage_service.get_file_bytes(image.file_path, current_user.id)
    return FastAPIResponse(content=file_bytes, media_type=image.mime_type)
