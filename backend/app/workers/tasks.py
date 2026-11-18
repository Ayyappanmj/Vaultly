import logging
import uuid
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.ocr_job import OCRJob
from app.models.receipt import Receipt
from app.services.ocr.duplicate import check_for_duplicate_receipt
from app.services.ocr.parser import parse_receipt_text
from app.services.ocr.preprocessor import preprocess_image
from app.services.ocr.provider import get_ocr_provider
from app.services.reminders import evaluate_and_create_reminders
from app.storage.service import storage_service
from app.workers.celery_app import celery_app

logger = logging.getLogger("vaultly.celery")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def process_ocr_task(self, job_id_str: str):
    """Asynchronous background worker task for OCR processing with automatic retry."""
    db = SessionLocal()
    try:
        job_id = uuid.UUID(job_id_str)
        job = db.query(OCRJob).filter(OCRJob.id == job_id).first()
        if not job:
            logger.error("OCR job %s not found", job_id_str)
            return

        job.status = "PROCESSING"
        db.commit()

        full_image_path = str(storage_service.base_dir / job.image_path)
        preprocessed = preprocess_image(full_image_path)
        provider = get_ocr_provider()
        raw_text = provider.extract_text(preprocessed)
        parsed = parse_receipt_text(raw_text)

        # Duplicate check
        is_dup, warning = check_for_duplicate_receipt(
            db=db,
            user_id=job.user_id,
            merchant_name=parsed.merchant_name,
            purchase_date=parsed.purchase_date,
            total_amount=parsed.total_amount,
            receipt_number=parsed.receipt_number,
            ocr_raw_text=raw_text,
        )
        parsed.is_duplicate = is_dup
        parsed.duplicate_warning = warning

        job.raw_text = raw_text
        job.parsed_data = parsed.model_dump_json()
        job.status = "COMPLETED"
        job.completed_at = datetime.now(timezone.utc)

        # Update receipt
        if job.receipt_id:
            receipt = db.query(Receipt).filter(Receipt.id == job.receipt_id).first()
            if receipt:
                if parsed.merchant_name:
                    receipt.merchant_name = parsed.merchant_name
                if parsed.purchase_date:
                    receipt.purchase_date = parsed.purchase_date
                if parsed.total_amount:
                    receipt.total_amount = parsed.total_amount
                receipt.status = "REVIEW_NEEDED" if not is_dup else "DUPLICATE_WARNING"
                if warning:
                    receipt.notes = f"[{warning}]".strip()

        db.commit()
        logger.info("OCR job %s completed successfully", job_id_str)

    except Exception as exc:
        logger.exception("Error processing OCR job %s: %s", job_id_str, exc)
        db.rollback()
        try:
            self.retry(exc=exc, countdown=2**self.request.retries)
        except Exception:
            job = db.query(OCRJob).filter(OCRJob.id == uuid.UUID(job_id_str)).first()
            if job:
                job.status = "FAILED"
                job.error_message = str(exc)
                db.commit()
    finally:
        db.close()


@celery_app.task
def generate_daily_reminders_task() -> int:
    """Scheduled Celery Beat task to evaluate expiring warranties, upcoming renewals, and trials."""
    db = SessionLocal()
    try:
        count = evaluate_and_create_reminders(db)
        logger.info("Scheduled reminder run completed: created %d notifications", count)
        return count
    finally:
        db.close()
