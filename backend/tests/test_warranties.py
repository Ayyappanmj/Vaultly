from datetime import datetime, timezone
from app.services.warranties import (
    add_months,
    calculate_warranty_status,
    suggest_warranty_from_purchase,
)


def test_add_months_leap_year_and_month_end():
    # Leap year case: Jan 31 + 1 month in non-leap year -> Feb 28
    d1 = datetime(2023, 1, 31, tzinfo=timezone.utc)
    res1 = add_months(d1, 1)
    assert res1.year == 2023
    assert res1.month == 2
    assert res1.day == 28

    # Leap year case: Jan 31 + 1 month in leap year (2024) -> Feb 29
    d2 = datetime(2024, 1, 31, tzinfo=timezone.utc)
    res2 = add_months(d2, 1)
    assert res2.year == 2024
    assert res2.month == 2
    assert res2.day == 29

    # Month end 31 to 30: May 31 + 1 month -> June 30
    d3 = datetime(2024, 5, 31, tzinfo=timezone.utc)
    res3 = add_months(d3, 1)
    assert res3.year == 2024
    assert res3.month == 6
    assert res3.day == 30


def test_warranty_status_calculation():
    now = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Active: 60 days in the future
    future_60 = datetime(2024, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert calculate_warranty_status(future_60, now) == "ACTIVE"

    # 2. Expiring soon: 10 days in future
    future_10 = datetime(2024, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
    assert calculate_warranty_status(future_10, now) == "EXPIRING_SOON"

    # 3. Expired: in the past
    past = datetime(2024, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert calculate_warranty_status(past, now) == "EXPIRED"


def test_warranty_suggestion():
    sugg1 = suggest_warranty_from_purchase("Apple MacBook Pro 16", "Apple")
    assert sugg1 is not None
    assert sugg1.suggested_duration_months == 12

    sugg2 = suggest_warranty_from_purchase("Samsung Smart Refrigerator", "Samsung")
    assert sugg2 is not None
    assert sugg2.suggested_duration_months == 24
