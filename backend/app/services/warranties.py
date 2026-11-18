import calendar
from datetime import datetime, timezone

from app.schemas.warranty import WarrantySuggestion

EXPIRING_SOON_DAYS = 30


def add_months(source_date: datetime, months: int) -> datetime:
    """Adds months to a datetime, handling month-end, leap year, and day-overflow correctly."""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    # Get max days in target month
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return source_date.replace(year=year, month=month, day=day)


def calculate_warranty_status(end_date: datetime, now: datetime | None = None) -> str:
    """Calculates warranty status:
    - ACTIVE: more than 30 days remaining
    - EXPIRING_SOON: between 0 and 30 days remaining
    - EXPIRED: past end date
    - UNKNOWN: if end_date is missing
    """
    if not end_date:
        return "UNKNOWN"

    current = now or datetime.now(timezone.utc)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)

    if current > end_date:
        return "EXPIRED"

    days_remaining = (end_date - current).days
    if days_remaining <= EXPIRING_SOON_DAYS:
        return "EXPIRING_SOON"

    return "ACTIVE"


def suggest_warranty_from_purchase(
    product_name: str, brand: str | None = None
) -> WarrantySuggestion | None:
    """Generates heuristic-based warranty suggestion based on product metadata."""
    name_lower = product_name.lower()

    if any(
        k in name_lower
        for k in [
            "laptop",
            "macbook",
            "computer",
            "desktop",
            "ipad",
            "tablet",
            "iphone",
            "phone",
        ]
    ):
        return WarrantySuggestion(
            product_name=product_name,
            suggested_duration_months=12,
            provider=brand or "Manufacturer",
            reason="Electronics typically come with a 1-year standard manufacturer warranty.",
        )
    if any(
        k in name_lower
        for k in [
            "refrigerator",
            "fridge",
            "washer",
            "dryer",
            "dishwasher",
            "oven",
            "tv",
            "television",
        ]
    ):
        return WarrantySuggestion(
            product_name=product_name,
            suggested_duration_months=24,
            provider=brand or "Manufacturer",
            reason="Major home appliances typically carry 2-year warranty coverage.",
        )
    if any(
        k in name_lower
        for k in ["headphone", "earbuds", "mouse", "keyboard", "cable", "charger"]
    ):
        return WarrantySuggestion(
            product_name=product_name,
            suggested_duration_months=12,
            provider=brand or "Manufacturer",
            reason="Accessories typically include a 1-year limited warranty.",
        )
    return None
