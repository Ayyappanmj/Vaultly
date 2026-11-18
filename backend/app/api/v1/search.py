from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.category import Category
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.subscription import Subscription
from app.models.user import User
from app.models.warranty import Warranty
from app.schemas.receipt import ReceiptResponse
from app.schemas.subscription import SubscriptionResponse
from app.schemas.warranty import WarrantyResponse

router = APIRouter(prefix="/search", tags=["Full-Text Search"])


@router.get("")
def search_vault(
    q: str = Query(..., min_length=1, description="Search query string"),
    doc_type: str | None = Query(
        default=None, description="receipt, warranty, subscription, or all"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Full-text and multi-field search across:
    - Receipt merchant, notes, receipt number, OCR raw text
    - Receipt line items (e.g. 'USB-C cable' matches receipt)
    - Categories
    - Warranties (provider, policy number, terms)
    - Subscriptions (service name, notes)
    """
    term = f"%{q.strip().lower()}%"
    results = {
        "query": q,
        "receipts": [],
        "warranties": [],
        "subscriptions": [],
        "total_matches": 0,
    }

    # 1. Search receipts (including line items match)
    if doc_type in {None, "all", "receipt"}:
        stmt = (
            select(Receipt)
            .distinct()
            .outerjoin(Receipt.items)
            .outerjoin(Receipt.category)
            .where(
                Receipt.user_id == current_user.id,
                Receipt.is_deleted.is_(False),
                or_(
                    Receipt.merchant_name.ilike(term),
                    Receipt.receipt_number.ilike(term),
                    Receipt.notes.ilike(term),
                    Receipt.ocr_raw_text.ilike(term),
                    ReceiptItem.description.ilike(term),
                    Category.name.ilike(term),
                ),
            )
            .options(joinedload(Receipt.category))
        )
        matched_receipts = db.execute(stmt).scalars().all()
        results["receipts"] = [
            ReceiptResponse.model_validate(r) for r in matched_receipts
        ]

    # 2. Search warranties
    if doc_type in {None, "all", "warranty"}:
        w_stmt = select(Warranty).where(
            Warranty.user_id == current_user.id,
            or_(
                Warranty.provider.ilike(term),
                Warranty.policy_number.ilike(term),
                Warranty.terms.ilike(term),
            ),
        )
        matched_warranties = db.execute(w_stmt).scalars().all()
        results["warranties"] = [
            WarrantyResponse.model_validate(w) for w in matched_warranties
        ]

    # 3. Search subscriptions
    if doc_type in {None, "all", "subscription"}:
        s_stmt = select(Subscription).where(
            Subscription.user_id == current_user.id,
            or_(
                Subscription.service_name.ilike(term),
                Subscription.notes.ilike(term),
            ),
        )
        matched_subs = db.execute(s_stmt).scalars().all()
        # compute equivalents
        from app.services.subscriptions import calculate_cost_equivalents

        sub_resps = []
        for s in matched_subs:
            m, a = calculate_cost_equivalents(s.amount, s.billing_frequency)
            sub_resps.append(
                SubscriptionResponse(
                    id=s.id,
                    user_id=s.user_id,
                    service_name=s.service_name,
                    billing_frequency=s.billing_frequency,
                    amount=s.amount,
                    currency=s.currency,
                    status=s.status,
                    start_date=s.start_date,
                    next_renewal_date=s.next_renewal_date,
                    trial_end_date=s.trial_end_date,
                    cancellation_date=s.cancellation_date,
                    monthly_equivalent=m,
                    annual_equivalent=a,
                    notes=s.notes,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        results["subscriptions"] = sub_resps

    results["total_matches"] = (
        len(results["receipts"])
        + len(results["warranties"])
        + len(results["subscriptions"])
    )
    return results
