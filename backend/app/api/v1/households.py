import json
import uuid
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.models.household import ExpenseSplit, Household, HouseholdMember
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.household import (
    ExpenseSplitCreate,
    ExpenseSplitResponse,
    HouseholdBalanceReport,
    HouseholdCreate,
    HouseholdMemberResponse,
    HouseholdResponse,
)
from app.services.splits import calculate_expense_splits, calculate_member_balances

router = APIRouter(prefix="/households", tags=["Households & Expense Splitting"])


@router.get("", response_model=list[HouseholdResponse])
def list_households(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Household)
        .join(HouseholdMember)
        .where(HouseholdMember.user_id == current_user.id)
        .options(joinedload(Household.members).joinedload(HouseholdMember.user))
    )
    households = db.execute(stmt).unique().scalars().all()

    result = []
    for h in households:
        m_resps = [
            HouseholdMemberResponse(
                id=m.id,
                user_id=m.user_id,
                role=m.role,
                joined_at=m.joined_at,
                email=m.user.email if m.user else None,
                full_name=m.user.full_name if m.user else None,
            )
            for m in h.members
        ]
        result.append(
            HouseholdResponse(
                id=h.id,
                name=h.name,
                created_by=h.created_by,
                created_at=h.created_at,
                members=m_resps,
            )
        )
    return result


@router.post("", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
def create_household(
    body: HouseholdCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    household = Household(name=body.name, created_by=current_user.id)
    db.add(household)
    db.flush()

    member = HouseholdMember(
        household_id=household.id, user_id=current_user.id, role="OWNER"
    )
    db.add(member)
    db.commit()

    return HouseholdResponse(
        id=household.id,
        name=household.name,
        created_by=household.created_by,
        created_at=household.created_at,
        members=[
            HouseholdMemberResponse(
                id=member.id,
                user_id=current_user.id,
                role="OWNER",
                joined_at=member.joined_at,
                email=current_user.email,
                full_name=current_user.full_name,
            )
        ],
    )


@router.post("/{household_id}/members", response_model=MessageResponse)
def add_member(
    household_id: uuid.UUID,
    email: str,
    role: str = "MEMBER",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify current user is owner or admin
    admin_member = db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == current_user.id,
            HouseholdMember.role.in_(["OWNER", "ADMIN"]),
        )
    ).scalar_one_or_none()

    if not admin_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only household owners/admins can invite members.",
        )

    target_user = db.execute(
        select(User).where(User.email == email.lower())
    ).scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found.",
        )

    existing = db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == target_user.id,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a household member.",
        )

    new_member = HouseholdMember(
        household_id=household_id, user_id=target_user.id, role=role.upper()
    )
    db.add(new_member)
    db.commit()
    return MessageResponse(
        message=f"Added {target_user.full_name or target_user.email} to household."
    )


@router.post(
    "/{household_id}/splits",
    response_model=ExpenseSplitResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_expense_split(
    household_id: uuid.UUID,
    body: ExpenseSplitCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Verify current user belongs to household
    membership = db.execute(
        select(HouseholdMember).where(
            HouseholdMember.household_id == household_id,
            HouseholdMember.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this household.",
        )

    members = (
        db.execute(
            select(HouseholdMember).where(HouseholdMember.household_id == household_id)
        )
        .scalars()
        .all()
    )
    member_ids = [m.user_id for m in members]

    try:
        shares_results = calculate_expense_splits(
            total_amount=body.total_amount,
            split_type=body.split_type,
            member_ids=member_ids,
            shares_input=body.shares,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    shares_data_json = json.dumps(
        [
            {"user_id": str(s.user_id), "share_amount": str(s.share_amount)}
            for s in shares_results
        ]
    )

    split = ExpenseSplit(
        household_id=household_id,
        receipt_id=body.receipt_id,
        paid_by=current_user.id,
        description=body.description,
        split_type=body.split_type.upper(),
        shares_data=shares_data_json,
        total_amount=body.total_amount,
        currency=body.currency.upper(),
        is_settled=False,
    )
    db.add(split)
    db.commit()
    db.refresh(split)

    return ExpenseSplitResponse(
        id=split.id,
        household_id=split.household_id,
        receipt_id=split.receipt_id,
        paid_by=split.paid_by,
        payer_name=current_user.full_name or current_user.email,
        description=split.description,
        split_type=split.split_type,
        total_amount=split.total_amount,
        currency=split.currency,
        is_settled=split.is_settled,
        shares=shares_results,
        created_at=split.created_at,
    )


@router.get("/{household_id}/balances", response_model=HouseholdBalanceReport)
def get_household_balances(
    household_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    members = (
        db.execute(
            select(HouseholdMember)
            .options(joinedload(HouseholdMember.user))
            .where(HouseholdMember.household_id == household_id)
        )
        .scalars()
        .all()
    )

    member_dicts = [
        {"id": m.user_id, "name": m.user.full_name if m.user else "Unknown"}
        for m in members
    ]

    splits = (
        db.execute(
            select(ExpenseSplit).where(
                ExpenseSplit.household_id == household_id,
                ExpenseSplit.is_settled.is_(False),
            )
        )
        .scalars()
        .all()
    )

    expense_dicts = []
    for s in splits:
        shares_raw = json.loads(s.shares_data)
        shares_parsed = [
            {
                "user_id": uuid.UUID(x["user_id"]),
                "share_amount": Decimal(x["share_amount"]),
            }
            for x in shares_raw
        ]
        expense_dicts.append(
            {
                "paid_by": s.paid_by,
                "total_amount": s.total_amount,
                "shares": shares_parsed,
            }
        )

    balances = calculate_member_balances(member_dicts, expense_dicts)
    return HouseholdBalanceReport(
        household_id=household_id, currency="USD", member_balances=balances
    )
