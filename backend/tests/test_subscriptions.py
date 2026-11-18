from datetime import datetime, timezone
from decimal import Decimal
from app.services.subscriptions import (
    calculate_cost_equivalents,
    calculate_next_renewal_date,
)


def test_calculate_cost_equivalents():
    # Weekly $10 -> annual $520, monthly = 520 / 12 = 43.33
    m, a = calculate_cost_equivalents(Decimal("10.00"), "WEEKLY")
    assert a == Decimal("520.00")
    assert m == Decimal("43.33")

    # Monthly $15 -> annual $180, monthly $15
    m, a = calculate_cost_equivalents(Decimal("15.00"), "MONTHLY")
    assert a == Decimal("180.00")
    assert m == Decimal("15.00")

    # Quarterly $30 -> annual $120, monthly $10
    m, a = calculate_cost_equivalents(Decimal("30.00"), "QUARTERLY")
    assert a == Decimal("120.00")
    assert m == Decimal("10.00")

    # Yearly $120 -> annual $120, monthly $10
    m, a = calculate_cost_equivalents(Decimal("120.00"), "YEARLY")
    assert a == Decimal("120.00")
    assert m == Decimal("10.00")


def test_next_renewal_date():
    start = datetime(2024, 1, 15, tzinfo=timezone.utc)
    ref = datetime(2024, 3, 1, tzinfo=timezone.utc)

    # Monthly renewal past March 1 should be March 15
    next_renew = calculate_next_renewal_date(start, "MONTHLY", ref)
    assert next_renew.year == 2024
    assert next_renew.month == 3
    assert next_renew.day == 15


def test_subscription_analytics_excludes_cancelled_and_paused(client, auth_headers):
    # 1. Active: $20/month
    client.post(
        "/api/v1/subscriptions",
        headers=auth_headers,
        json={
            "service_name": "Active Music",
            "billing_frequency": "MONTHLY",
            "amount": 20.00,
            "status": "ACTIVE",
            "start_date": "2024-01-01T00:00:00Z",
        },
    )

    # 2. Cancelled: $50/month
    client.post(
        "/api/v1/subscriptions",
        headers=auth_headers,
        json={
            "service_name": "Old Cloud Storage",
            "billing_frequency": "MONTHLY",
            "amount": 50.00,
            "status": "CANCELLED",
            "start_date": "2024-01-01T00:00:00Z",
        },
    )

    res = client.get("/api/v1/subscriptions/analytics", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_active_count"] == 1
    assert Decimal(str(data["total_monthly_spend"])) == Decimal("20.00")
