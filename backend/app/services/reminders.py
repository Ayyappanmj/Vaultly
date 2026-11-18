from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.subscription import Subscription
from app.models.warranty import Warranty


def evaluate_and_create_reminders(db: Session, now: datetime | None = None) -> int:
    """Evaluates upcoming expirations and renewals and creates in-app notifications
    with strict deduplication keys so notifications are NEVER created twice.
    Returns count of created notifications.
    """
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    notifications_created = 0

    # 1. Warranty reminders: 30 days, 7 days, 1 day
    warranty_rules = [30, 7, 1]
    for days_ahead in warranty_rules:
        target_start = current_time + timedelta(days=days_ahead - 1)
        target_end = current_time + timedelta(days=days_ahead + 1)

        stmt = select(Warranty).where(
            Warranty.status == "ACTIVE",
            Warranty.end_date >= target_start,
            Warranty.end_date <= target_end,
        )
        warranties = db.execute(stmt).scalars().all()

        for w in warranties:
            due_date_str = w.end_date.strftime("%Y-%m-%d")
            dedup_key = f"warranty:{w.id}:{days_ahead}d:{due_date_str}"

            # Check if notification already exists
            existing = db.execute(
                select(Notification).where(Notification.deduplication_key == dedup_key)
            ).scalar_one_or_none()

            if not existing:
                title = f"Warranty Expiring in {days_ahead} Day{'s' if days_ahead > 1 else ''}"
                message = f"Your warranty for {w.provider} policy {w.policy_number or ''} expires on {due_date_str}."
                notification = Notification(
                    user_id=w.user_id,
                    title=title,
                    message=message,
                    notification_type="WARRANTY",
                    entity_type="warranty",
                    entity_id=str(w.id),
                    deduplication_key=dedup_key,
                    created_at=current_time,
                )
                db.add(notification)
                notifications_created += 1

    # 2. Subscription reminders: 7 days, 3 days, 1 day
    sub_rules = [7, 3, 1]
    for days_ahead in sub_rules:
        target_start = current_time + timedelta(days=days_ahead - 1)
        target_end = current_time + timedelta(days=days_ahead + 1)

        stmt = select(Subscription).where(
            Subscription.status == "ACTIVE",
            Subscription.next_renewal_date >= target_start,
            Subscription.next_renewal_date <= target_end,
        )
        subscriptions = db.execute(stmt).scalars().all()

        for s in subscriptions:
            due_date_str = s.next_renewal_date.strftime("%Y-%m-%d")
            dedup_key = f"subscription:{s.id}:{days_ahead}d:{due_date_str}"

            existing = db.execute(
                select(Notification).where(Notification.deduplication_key == dedup_key)
            ).scalar_one_or_none()

            if not existing:
                title = f"Subscription Renewal in {days_ahead} Day{'s' if days_ahead > 1 else ''}"
                message = f"Your subscription for {s.service_name} will renew for {s.currency} {s.amount} on {due_date_str}."
                notification = Notification(
                    user_id=s.user_id,
                    title=title,
                    message=message,
                    notification_type="SUBSCRIPTION",
                    entity_type="subscription",
                    entity_id=str(s.id),
                    deduplication_key=dedup_key,
                    created_at=current_time,
                )
                db.add(notification)
                notifications_created += 1

    # 3. Trial expiration reminders: 48 hours
    trial_target_start = current_time
    trial_target_end = current_time + timedelta(hours=48)
    trial_subs = (
        db.execute(
            select(Subscription).where(
                Subscription.status == "TRIAL",
                Subscription.trial_end_date.isnot(None),
                Subscription.trial_end_date >= trial_target_start,
                Subscription.trial_end_date <= trial_target_end,
            )
        )
        .scalars()
        .all()
    )

    for s in trial_subs:
        if s.trial_end_date:
            due_str = s.trial_end_date.strftime("%Y-%m-%d")
            dedup_key = f"trial:{s.id}:48h:{due_str}"
            existing = db.execute(
                select(Notification).where(Notification.deduplication_key == dedup_key)
            ).scalar_one_or_none()

            if not existing:
                title = "Free Trial Expiring in 48 Hours"
                message = f"Your free trial for {s.service_name} ends on {due_str}. Cancel now if you do not want to be charged."
                notification = Notification(
                    user_id=s.user_id,
                    title=title,
                    message=message,
                    notification_type="TRIAL",
                    entity_type="subscription",
                    entity_id=str(s.id),
                    deduplication_key=dedup_key,
                    created_at=current_time,
                )
                db.add(notification)
                notifications_created += 1

    if notifications_created > 0:
        db.commit()

    return notifications_created
