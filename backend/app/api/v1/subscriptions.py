import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.subscription import (
    SubscriptionAnalytics,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from app.services.subscriptions import (
    calculate_cost_equivalents,
    calculate_next_renewal_date,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


def _to_response(sub: Subscription) -> SubscriptionResponse:
    monthly, annual = calculate_cost_equivalents(sub.amount, sub.billing_frequency)
    return SubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        service_name=sub.service_name,
        billing_frequency=sub.billing_frequency,
        amount=sub.amount,
        currency=sub.currency,
        status=sub.status,
        start_date=sub.start_date,
        next_renewal_date=sub.next_renewal_date,
        trial_end_date=sub.trial_end_date,
        cancellation_date=sub.cancellation_date,
        monthly_equivalent=monthly,
        annual_equivalent=annual,
        notes=sub.notes,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@router.get("", response_model=PaginatedResponse[SubscriptionResponse])
def list_subscriptions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = select(Subscription).where(Subscription.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Subscription.status == status_filter.upper())

    stmt = stmt.order_by(Subscription.next_renewal_date.asc())
    subs = db.execute(stmt).scalars().all()

    responses = [_to_response(s) for s in subs]
    paginated = responses[(page - 1) * page_size : page * page_size]

    return PaginatedResponse[SubscriptionResponse](
        items=paginated,
        total=len(responses),
        page=page,
        page_size=page_size,
        total_pages=(len(responses) + page_size - 1) // page_size if responses else 1,
    )


@router.get("/analytics", response_model=SubscriptionAnalytics)
def get_subscription_analytics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    subs = (
        db.execute(
            select(Subscription).where(
                Subscription.user_id == current_user.id,
                Subscription.status.in_(["ACTIVE", "TRIAL"]),
            )
        )
        .scalars()
        .all()
    )

    total_monthly = Decimal("0.00")
    total_annual = Decimal("0.00")
    now = datetime.now(timezone.utc)
    in_30_days = now + timedelta(days=30)
    upcoming: list[SubscriptionResponse] = []

    for s in subs:
        m, a = calculate_cost_equivalents(s.amount, s.billing_frequency)
        total_monthly += m
        total_annual += a
        resp = _to_response(s)
        # Check upcoming renewals
        if s.next_renewal_date:
            renew_dt = (
                s.next_renewal_date
                if s.next_renewal_date.tzinfo
                else s.next_renewal_date.replace(tzinfo=timezone.utc)
            )
            if now <= renew_dt <= in_30_days:
                upcoming.append(resp)

    upcoming.sort(key=lambda x: x.next_renewal_date)

    return SubscriptionAnalytics(
        total_active_count=len(subs),
        total_monthly_spend=round(total_monthly, 2),
        total_annual_spend=round(total_annual, 2),
        currency="USD",
        upcoming_renewals_next_30_days=upcoming,
    )


@router.post(
    "", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED
)
def create_subscription(
    body: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    next_renewal = body.next_renewal_date or calculate_next_renewal_date(
        body.start_date, body.billing_frequency
    )

    subscription = Subscription(
        user_id=current_user.id,
        service_name=body.service_name,
        billing_frequency=body.billing_frequency.upper(),
        amount=body.amount,
        currency=body.currency.upper(),
        status=body.status.upper(),
        start_date=body.start_date,
        next_renewal_date=next_renewal,
        trial_end_date=body.trial_end_date,
        notes=body.notes,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return _to_response(subscription)


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    subscription = db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id, Subscription.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
        )

    return _to_response(subscription)


@router.put("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: uuid.UUID,
    body: SubscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    subscription = db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id, Subscription.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
        )

    for field, val in body.model_dump(exclude_unset=True).items():
        if field == "billing_frequency" and val:
            val = val.upper()
        if field == "status" and val:
            val = val.upper()
        setattr(subscription, field, val)

    if body.billing_frequency or body.start_date:
        subscription.next_renewal_date = (
            body.next_renewal_date
            or calculate_next_renewal_date(
                subscription.start_date, subscription.billing_frequency
            )
        )

    db.commit()
    db.refresh(subscription)
    return _to_response(subscription)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Marks subscription as cancelled in Vaultly records.
    Never claims or attempts external cancellation.
    """
    subscription = db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id, Subscription.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
        )

    subscription.status = "CANCELLED"
    subscription.cancellation_date = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscription)
    return _to_response(subscription)


@router.delete("/{subscription_id}", response_model=MessageResponse)
def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    subscription = db.execute(
        select(Subscription).where(
            Subscription.id == subscription_id, Subscription.user_id == current_user.id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
        )

    db.delete(subscription)
    db.commit()
    return MessageResponse(message="Subscription deleted successfully.")
