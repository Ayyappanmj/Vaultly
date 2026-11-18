import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.purchase import Purchase
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.purchase import PurchaseCreate, PurchaseResponse, PurchaseUpdate

router = APIRouter(prefix="/purchases", tags=["Purchases"])


@router.get("", response_model=PaginatedResponse[PurchaseResponse])
def list_purchases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Purchase)
        .where(Purchase.user_id == current_user.id)
        .order_by(Purchase.purchase_date.desc())
    )
    items = (
        db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    )
    total = len(items)

    return PaginatedResponse[PurchaseResponse](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=1,
    )


@router.post("", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def create_purchase(
    body: PurchaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    purchase = Purchase(
        user_id=current_user.id,
        receipt_id=body.receipt_id,
        product_name=body.product_name,
        brand=body.brand,
        model_number=body.model_number,
        serial_number=body.serial_number,
        purchase_date=body.purchase_date,
        price=body.price,
        currency=body.currency.upper(),
        notes=body.notes,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(
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
    return purchase


@router.put("/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(
    purchase_id: uuid.UUID,
    body: PurchaseUpdate,
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

    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(purchase, field, val)

    db.commit()
    db.refresh(purchase)
    return purchase


@router.delete("/{purchase_id}", response_model=MessageResponse)
def delete_purchase(
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

    db.delete(purchase)
    db.commit()
    return MessageResponse(message="Purchase deleted successfully.")
