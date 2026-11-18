from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.receipt import Receipt
from app.models.user import User
from app.schemas.common import MessageResponse
from app.services.reports import (
    generate_expense_pdf,
    generate_receipts_csv,
    parse_receipts_csv,
)

router = APIRouter(prefix="/reports", tags=["Reports & Export"])


@router.get("/export/csv")
def export_csv(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Receipt)
        .options(joinedload(Receipt.category))
        .where(Receipt.user_id == current_user.id, Receipt.is_deleted.is_(False))
    )
    if start_date:
        stmt = stmt.where(Receipt.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(Receipt.purchase_date <= end_date)

    receipts = db.execute(stmt.order_by(Receipt.purchase_date.desc())).scalars().all()

    receipt_dicts = []
    for r in receipts:
        receipt_dicts.append(
            {
                "id": r.id,
                "purchase_date": r.purchase_date,
                "merchant_name": r.merchant_name,
                "total_amount": r.total_amount,
                "currency": r.currency,
                "category_name": r.category.name if r.category else "Uncategorized",
                "payment_method": r.payment_method or "",
                "receipt_number": r.receipt_number or "",
                "notes": r.notes or "",
            }
        )

    csv_data = generate_receipts_csv(receipt_dicts)
    return FastAPIResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=receipts-export.csv"},
    )


@router.post("/import/csv", response_model=MessageResponse)
async def import_csv(
    file: UploadFile,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    rows = parse_receipts_csv(csv_text)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid receipt records found in CSV.",
        )

    created_count = 0
    for r in rows:
        receipt = Receipt(
            user_id=current_user.id,
            merchant_name=r["merchant_name"],
            purchase_date=r["purchase_date"],
            total_amount=r["total_amount"],
            currency=r["currency"] or "USD",
            payment_method=r["payment_method"],
            receipt_number=r["receipt_number"],
            notes=r["notes"],
            status="CONFIRMED",
            sync_version=1,
        )
        db.add(receipt)
        created_count += 1

    db.commit()
    return MessageResponse(message=f"Successfully imported {created_count} receipts.")


@router.get("/export/pdf")
def export_pdf(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Receipt)
        .options(joinedload(Receipt.category))
        .where(Receipt.user_id == current_user.id, Receipt.is_deleted.is_(False))
    )
    if start_date:
        stmt = stmt.where(Receipt.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(Receipt.purchase_date <= end_date)

    receipts = db.execute(stmt.order_by(Receipt.purchase_date.desc())).scalars().all()

    receipt_dicts = []
    total_spent = Decimal("0.00")
    for r in receipts:
        total_spent += r.total_amount
        receipt_dicts.append(
            {
                "id": r.id,
                "purchase_date": r.purchase_date,
                "merchant_name": r.merchant_name,
                "total_amount": r.total_amount,
                "currency": r.currency,
                "category_name": r.category.name if r.category else "Uncategorized",
                "payment_method": r.payment_method or "",
                "receipt_number": r.receipt_number or "",
                "notes": r.notes or "",
            }
        )

    pdf_bytes = generate_expense_pdf(
        user_name=current_user.full_name or current_user.email,
        receipts=receipt_dicts,
        total_spent=total_spent,
        currency="USD",
    )

    return FastAPIResponse(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=expense-report.pdf"},
    )
