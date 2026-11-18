import uuid
from decimal import Decimal
from app.schemas.household import ShareItem
from app.services.splits import calculate_expense_splits, calculate_member_balances


def test_equal_split_penny_rounding_integrity():
    # $100.00 split among 3 people: $33.34 + $33.33 + $33.33 = $100.00
    u1, u2, u3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    members = [u1, u2, u3]
    total = Decimal("100.00")

    splits = calculate_expense_splits(
        total_amount=total, split_type="EQUAL", member_ids=members
    )
    assert len(splits) == 3
    shares = [s.share_amount for s in splits]
    assert shares[0] == Decimal("33.34")
    assert shares[1] == Decimal("33.33")
    assert shares[2] == Decimal("33.33")
    assert sum(shares) == total  # EXACT integrity guarantee!


def test_percentage_split_integrity():
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    total = Decimal("75.50")
    shares_input = [
        ShareItem(user_id=u1, percentage=Decimal("60.0")),
        ShareItem(user_id=u2, percentage=Decimal("40.0")),
    ]

    splits = calculate_expense_splits(
        total_amount=total,
        split_type="PERCENTAGE",
        member_ids=[u1, u2],
        shares_input=shares_input,
    )
    assert len(splits) == 2
    assert sum(s.share_amount for s in splits) == total


def test_member_balances():
    u1, u2 = uuid.uuid4(), uuid.uuid4()
    members = [{"id": u1, "name": "User 1"}, {"id": u2, "name": "User 2"}]

    # User 1 paid $100, split $50/$50
    expenses = [
        {
            "paid_by": u1,
            "total_amount": Decimal("100.00"),
            "shares": [
                {"user_id": u1, "share_amount": Decimal("50.00")},
                {"user_id": u2, "share_amount": Decimal("50.00")},
            ],
        }
    ]

    balances = calculate_member_balances(members, expenses)
    b1 = next(b for b in balances if b.user_id == u1)
    b2 = next(b for b in balances if b.user_id == u2)

    assert b1.total_paid == Decimal("100.00")
    assert b1.total_owed == Decimal("50.00")
    assert b1.net_balance == Decimal("50.00")  # User 1 is owed $50

    assert b2.total_paid == Decimal("0.00")
    assert b2.total_owed == Decimal("50.00")
    assert b2.net_balance == Decimal("-50.00")  # User 2 owes $50
