import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.ocr_job import OCRJob
from app.models.receipt import Receipt
from app.models.receipt_image import ReceiptImage
from app.models.receipt_item import ReceiptItem
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.ocr import OCRJobResponse, OCRReviewRequest, ParsedReceiptData
from app.services.ocr.duplicate import check_for_duplicate_receipt
from app.services.ocr.parser import parse_receipt_text
from app.services.ocr.preprocessor import compute_perceptual_hash, preprocess_image
from app.services.ocr.provider import get_ocr_provider
from app.storage.service import storage_service

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post(
    "/process", response_model=OCRJobResponse, status_code=status.HTTP_202_ACCEPTED
)
async def submit_ocr_job(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Submits an image for OCR processing. Saves image, creates job, and processes
    or enqueues OCR asynchronously without blocking the client.
    """
    content = await file.read()
    mime_type = storage_service.validate_file(file, content)
    rel_path, file_hash, size = storage_service.save_file(
        content, file.filename or "receipt.jpg", current_user.id
    )

    full_image_path = str(storage_service.base_dir / rel_path)
    p_hash = compute_perceptual_hash(full_image_path) if "image" in mime_type else None

    # Create unconfirmed receipt container
    receipt = Receipt(
        user_id=current_user.id,
        merchant_name="Processing Receipt...",
        purchase_date=datetime.now(timezone.utc),
        total_amount=0,
        currency="USD",
        status="PENDING",
    )
    db.add(receipt)
    db.flush()

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

    job = OCRJob(
        user_id=current_user.id,
        receipt_id=receipt.id,
        image_path=rel_path,
        status="PROCESSING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Perform processing (or Celery task)
    try:
        preprocessed = preprocess_image(full_image_path)
        provider = get_ocr_provider()
        raw_text = provider.extract_text(preprocessed)
        parsed = parse_receipt_text(raw_text)

        # Check duplicate
        is_dup, warning = check_for_duplicate_receipt(
            db=db,
            user_id=current_user.id,
            merchant_name=parsed.merchant_name,
            purchase_date=parsed.purchase_date,
            total_amount=parsed.total_amount,
            receipt_number=parsed.receipt_number,
            ocr_raw_text=raw_text,
            perceptual_hash=p_hash,
        )
        parsed.is_duplicate = is_dup
        parsed.duplicate_warning = warning

        job.raw_text = raw_text
        job.parsed_data = parsed.model_dump_json()
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)

        # Update receipt provisional values
        if parsed.merchant_name:
            receipt.merchant_name = parsed.merchant_name
        if parsed.purchase_date:
            receipt.purchase_date = parsed.purchase_date
        if parsed.total_amount:
            receipt.total_amount = parsed.total_amount
        if parsed.subtotal:
            receipt.subtotal = parsed.subtotal
        if parsed.tax_amount:
            receipt.tax_amount = parsed.tax_amount
        receipt.currency = parsed.currency
        receipt.receipt_number = parsed.receipt_number
        receipt.payment_method = parsed.payment_method
        receipt.ocr_raw_text = raw_text
        receipt.status = "REVIEW_NEEDED" if not is_dup else "DUPLICATE_WARNING"
        if warning:
            receipt.notes = f"[{warning}]".strip()

        db.commit()
        db.refresh(job)

    except Exception as exc:
        job.status = "FAILED"
        job.error_message = str(exc)
        receipt.status = "REVIEW_NEEDED"
        receipt.merchant_name = "Unrecognized Receipt"
        db.commit()
        db.refresh(job)

    parsed_obj = (
        ParsedReceiptData.model_validate_json(job.parsed_data)
        if job.parsed_data
        else None
    )
    return OCRJobResponse(
        id=job.id,
        user_id=job.user_id,
        receipt_id=job.receipt_id,
        status=job.status,
        raw_text=job.raw_text,
        parsed_data=parsed_obj,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/jobs/{job_id}", response_model=OCRJobResponse)
def get_ocr_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.execute(
        select(OCRJob).where(OCRJob.id == job_id, OCRJob.user_id == current_user.id)
    ).scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="OCR job not found."
        )

    parsed_obj = (
        ParsedReceiptData.model_validate_json(job.parsed_data)
        if job.parsed_data
        else None
    )
    return OCRJobResponse(
        id=job.id,
        user_id=job.user_id,
        receipt_id=job.receipt_id,
        status=job.status,
        raw_text=job.raw_text,
        parsed_data=parsed_obj,
        error_message=job.error_message,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.post("/jobs/{job_id}/review", response_model=MessageResponse)
def review_ocr_job(
    job_id: uuid.UUID,
    review: OCRReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    job = db.execute(
        select(OCRJob).where(OCRJob.id == job_id, OCRJob.user_id == current_user.id)
    ).scalar_one_or_none()

    if not job or not job.receipt_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OCR job or associated receipt not found.",
        )

    receipt = db.execute(
        select(Receipt).where(
            Receipt.id == job.receipt_id, Receipt.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found."
        )

    action = review.action.upper()
    if action == "CANCEL":
        receipt.is_deleted = True
        db.commit()
        return MessageResponse(message="Receipt creation cancelled and discarded.")

    if action in {"CONFIRM", "EDIT"}:
        if review.merchant_name:
            receipt.merchant_name = review.merchant_name
        if review.purchase_date:
            receipt.purchase_date = review.purchase_date
        if review.total_amount is not None:
            receipt.total_amount = review.total_amount
        if review.subtotal is not None:
            receipt.subtotal = review.subtotal
        if review.tax_amount is not None:
            receipt.tax_amount = review.tax_amount
        if review.currency:
            receipt.currency = review.currency
        if review.category_id:
            receipt.category_id = review.category_id
        if review.notes:
            receipt.notes = review.notes

        receipt.status = "CONFIRMED"
        receipt.sync_version += 1

        # Save line items if provided
        if review.line_items:
            for item_data in review.line_items:
                item = ReceiptItem(
                    receipt_id=receipt.id,
                    description=item_data.description,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.total_price,
                    category_id=review.category_id,
                )
                db.add(item)

        db.commit()
        return MessageResponse(message="Receipt confirmed successfully.")

    if action == "RETRY":
        job.status = "PROCESSING"
        db.commit()
        return MessageResponse(message="OCR job queued for retry.")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported action '{action}'.",
    )
