from datetime import datetime, timedelta, timezone
from app.models.warranty import Warranty
from app.models.subscription import Subscription
from app.services.reminders import evaluate_and_create_reminders


def test_reminders_creation_and_deduplication(db_session, test_user):
    now = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Warranty expiring in 30 days
    w = Warranty(
        user_id=test_user.id,
        provider="Gadget Care",
        duration_months=12,
        start_date=now - timedelta(days=335),
        end_date=now + timedelta(days=30),
        status="ACTIVE",
    )
    db_session.add(w)

    # 2. Subscription renewing in 7 days
    s = Subscription(
        user_id=test_user.id,
        service_name="Cloud Music",
        billing_frequency="MONTHLY",
        amount=10.00,
        currency="USD",
        status="ACTIVE",
        start_date=now - timedelta(days=23),
        next_renewal_date=now + timedelta(days=7),
    )
    db_session.add(s)
    db_session.commit()

    # First evaluation: 2 notifications created
    count1 = evaluate_and_create_reminders(db_session, now)
    assert count1 == 2

    # Second evaluation on the same day: deduplication key MUST prevent duplicate creation!
    count2 = evaluate_and_create_reminders(db_session, now)
    assert count2 == 0
