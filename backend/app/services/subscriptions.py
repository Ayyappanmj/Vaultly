from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.services.warranties import add_months


def calculate_next_renewal_date(
    start_date: datetime, billing_frequency: str, from_date: datetime | None = None
) -> datetime:
    """Calculates next upcoming renewal date for any frequency from a reference date."""
    ref = from_date or datetime.now(timezone.utc)
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)

    freq = billing_frequency.upper()
    current = start_date

    while current <= ref:
        if freq == "WEEKLY":
            current += timedelta(days=7)
        elif freq == "MONTHLY":
            current = add_months(current, 1)
        elif freq == "QUARTERLY":
            current = add_months(current, 3)
        elif freq == "HALF_YEARLY":
            current = add_months(current, 6)
        elif freq == "YEARLY":
            current = add_months(current, 12)
        else:  # CUSTOM defaults to 1 month
            current = add_months(current, 1)

    return current


def calculate_cost_equivalents(
    amount: Decimal, billing_frequency: str
) -> tuple[Decimal, Decimal]:
    """Calculates (monthly_equivalent, annual_equivalent) for a given amount and frequency.
    Weekly: monthly = amount * 52 / 12, annual = amount * 52
    Monthly: monthly = amount, annual = amount * 12
    Quarterly: monthly = amount / 3, annual = amount * 4
    Half-yearly: monthly = amount / 6, annual = amount * 2
    Yearly: monthly = amount / 12, annual = amount
    """
    freq = billing_frequency.upper()

    if freq == "WEEKLY":
        annual = amount * Decimal("52")
        monthly = (amount * Decimal("52")) / Decimal("12")
    elif freq == "MONTHLY":
        monthly = amount
        annual = amount * Decimal("12")
    elif freq == "QUARTERLY":
        monthly = amount / Decimal("3")
        annual = amount * Decimal("4")
    elif freq == "HALF_YEARLY":
        monthly = amount / Decimal("6")
        annual = amount * Decimal("2")
    elif freq == "YEARLY":
        monthly = amount / Decimal("12")
        annual = amount
    else:  # CUSTOM / default
        monthly = amount
        annual = amount * Decimal("12")

    return round(monthly, 2), round(annual, 2)
