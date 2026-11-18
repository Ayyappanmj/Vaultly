import uuid
from decimal import Decimal
from app.schemas.household import MemberBalance, ShareItem, ShareResult


def calculate_expense_splits(
    total_amount: Decimal,
    split_type: str,
    member_ids: list[uuid.UUID],
    shares_input: list[ShareItem] | None = None,
) -> list[ShareResult]:
    """Calculates deterministic splits where the sum of calculated shares
    EXACTLY equals the total amount to the penny, distributing rounding cents
    fairly across members.
    """
    if not member_ids:
        raise ValueError("At least one member is required for expense splitting.")

    st = split_type.upper()
    n = len(member_ids)
    results: list[ShareResult] = []

    if st == "EQUAL":
        base_share = (total_amount / Decimal(n)).quantize(Decimal("0.01"))
        allocated = base_share * Decimal(n)
        remainder = total_amount - allocated  # can be positive or negative cents

        # Distribute cents to first |remainder / 0.01| members
        cents = int((remainder * 100).to_integral_value())
        for i, m_id in enumerate(member_ids):
            adjustment = Decimal("0.01") if i < cents else Decimal("0.00")
            share = base_share + adjustment
            results.append(ShareResult(user_id=m_id, share_amount=share))

    elif st == "PERCENTAGE":
        if not shares_input:
            raise ValueError("Shares input required for percentage split.")
        input_map = {s.user_id: (s.percentage or Decimal("0")) for s in shares_input}
        total_pct = sum(input_map.values())
        if abs(total_pct - Decimal("100")) > Decimal("0.01"):
            raise ValueError(f"Percentages must sum to 100%, got {total_pct}%")

        allocated = Decimal("0.00")
        for m_id in member_ids:
            pct = input_map.get(m_id, Decimal("0"))
            share = ((total_amount * pct) / Decimal("100")).quantize(Decimal("0.01"))
            allocated += share
            results.append(ShareResult(user_id=m_id, share_amount=share))

        # Reconcile rounding discrepancy to match total_amount
        diff = total_amount - allocated
        if results and diff != Decimal("0.00"):
            results[0].share_amount += diff

    elif st == "EXACT":
        if not shares_input:
            raise ValueError("Shares input required for exact split.")
        input_map = {s.user_id: (s.exact_amount or Decimal("0")) for s in shares_input}
        allocated = sum(input_map.values())
        if allocated != total_amount:
            raise ValueError(
                f"Exact shares sum ({allocated}) must equal total amount ({total_amount})."
            )
        for m_id in member_ids:
            results.append(
                ShareResult(
                    user_id=m_id, share_amount=input_map.get(m_id, Decimal("0"))
                )
            )

    # Assert integrity: sum of parts MUST equal total_amount exactly
    actual_sum = sum(r.share_amount for r in results)
    assert actual_sum == total_amount, f"Split sum {actual_sum} != total {total_amount}"

    return results


def calculate_member_balances(
    members: list[dict],  # list of {id, name}
    expenses: list[
        dict
    ],  # list of {paid_by, total_amount, shares: [{user_id, share_amount}]}
) -> list[MemberBalance]:
    """Calculates each member's net balance:
    net_balance = total_paid - total_owed
    Positive = member is owed money
    Negative = member owes money to others
    """
    paid_map = {m["id"]: Decimal("0.00") for m in members}
    owed_map = {m["id"]: Decimal("0.00") for m in members}

    for exp in expenses:
        payer = exp["paid_by"]
        if payer in paid_map:
            paid_map[payer] += exp["total_amount"]
        for share in exp.get("shares", []):
            u_id = share["user_id"]
            if u_id in owed_map:
                owed_map[u_id] += share["share_amount"]

    balances = []
    for m in members:
        uid = m["id"]
        total_p = paid_map.get(uid, Decimal("0.00"))
        total_o = owed_map.get(uid, Decimal("0.00"))
        net = total_p - total_o
        balances.append(
            MemberBalance(
                user_id=uid,
                full_name=m.get("name", "Unknown"),
                total_paid=total_p,
                total_owed=total_o,
                net_balance=net,
            )
        )
    return balances
