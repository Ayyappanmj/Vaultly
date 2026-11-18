import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.purchase import Purchase
from app.models.user import User
from app.models.warranty import Warranty
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.warranty import (
    WarrantyCreate,
    WarrantyResponse,
    WarrantySuggestion,
    WarrantyUpdate,
)
from app.services.warranties import (
    add_months,
    calculate_warranty_status,
    suggest_warranty_from_purchase,
)

router = APIRouter(prefix="/warranties", tags=["Warranties"])


@router.get("", response_model=PaginatedResponse[WarrantyResponse])
def list_warranties(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Warranty).where(Warranty.user_id == current_user.id)
    items = db.execute(stmt).scalars().all()

    # Recalculate dynamic statuses based on current date
    now = datetime.now(timezone.utc)
    for w in items:
        new_status = calculate_warranty_status(w.end_date, now)
        if w.status != new_status:
            w.status = new_status
    db.commit()

    if status_filter:
        items = [w for w in items if w.status == status_filter.upper()]

    items.sort(key=lambda w: w.end_date)
    paginated_items = items[(page - 1) * page_size : page * page_size]

    return PaginatedResponse[WarrantyResponse](
        items=paginated_items,
        total=len(items),
        page=page,
        page_size=page_size,
        total_pages=(len(items) + page_size - 1) // page_size if items else 1,
    )


@router.post("", response_model=WarrantyResponse, status_code=status.HTTP_201_CREATED)
def create_warranty(
    body: WarrantyCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Compute end date from start_date + duration_months if not explicitly provided
    end_date = body.end_date or add_months(body.start_date, body.duration_months)
    warranty_status = calculate_warranty_status(end_date)

    warranty = Warranty(
        user_id=current_user.id,
        purchase_id=body.purchase_id,
        receipt_id=body.receipt_id,
        provider=body.provider,
        duration_months=body.duration_months,
        start_date=body.start_date,
        end_date=end_date,
        policy_number=body.policy_number,
        terms=body.terms,
        reminder_days=body.reminder_days,
        status=warranty_status,
    )
    db.add(warranty)
    db.commit()
    db.refresh(warranty)
    return warranty


@router.get("/suggest", response_model=WarrantySuggestion | None)
def get_warranty_suggestion(
    purchase_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    purchase = db.execute(
        select(Purchase).where(
            Purchase.id == purchase_id, Purchase.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not purchase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found."
        )

    suggestion = suggest_warranty_from_purchase(purchase.product_name, purchase.brand)
    return suggestion


@router.get("/{warranty_id}", response_model=WarrantyResponse)
def get_warranty(
    warranty_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    warranty = db.execute(
        select(Warranty).where(
            Warranty.id == warranty_id, Warranty.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warranty not found."
        )

    warranty.status = calculate_warranty_status(warranty.end_date)
    db.commit()
    return warranty


@router.put("/{warranty_id}", response_model=WarrantyResponse)
def update_warranty(
    warranty_id: uuid.UUID,
    body: WarrantyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    warranty = db.execute(
        select(Warranty).where(
            Warranty.id == warranty_id, Warranty.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warranty not found."
        )

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(warranty, field, val)

    if body.duration_months or body.start_date:
        warranty.end_date = body.end_date or add_months(
            warranty.start_date, warranty.duration_months
        )

    warranty.status = calculate_warranty_status(warranty.end_date)
    db.commit()
    db.refresh(warranty)
    return warranty


@router.delete("/{warranty_id}", response_model=MessageResponse)
def delete_warranty(
    warranty_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    warranty = db.execute(
        select(Warranty).where(
            Warranty.id == warranty_id, Warranty.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not warranty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Warranty not found."
        )

    db.delete(warranty)
    db.commit()
    return MessageResponse(message="Warranty deleted successfully.")
