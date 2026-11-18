import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.category import Category
from app.models.household import ExpenseSplit, Household, HouseholdMember
from app.models.notification import Notification
from app.models.purchase import Purchase
from app.models.receipt import Receipt
from app.models.receipt_item import ReceiptItem
from app.models.subscription import Subscription
from app.models.user import User
from app.models.warranty import Warranty
from app.services.warranties import add_months, calculate_warranty_status


def seed_database():
    print("==> Seeding Vaultly database with realistic fictional data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Create or get primary demo user
        demo_email = "demo@vaultly.app"
        demo_user = db.execute(
            select(User).where(User.email == demo_email)
        ).scalar_one_or_none()
        if not demo_user:
            demo_user = User(
                email=demo_email,
                hashed_password=hash_password("Password123!"),
                full_name="Alex Mercer (Demo)",
                is_active=True,
                is_verified=True,
            )
            db.add(demo_user)
            db.flush()
            print("  Created demo user: demo@vaultly.app / Password123!")
        else:
            print("  Demo user already exists.")

        # 2. Create second user for household splits
        alice_email = "alice@vaultly.app"
        alice_user = db.execute(
            select(User).where(User.email == alice_email)
        ).scalar_one_or_none()
        if not alice_user:
            alice_user = User(
                email=alice_email,
                hashed_password=hash_password("Password123!"),
                full_name="Alice Vance (Roommate)",
                is_active=True,
                is_verified=True,
            )
            db.add(alice_user)
            db.flush()
            print("  Created roommate user: alice@vaultly.app / Password123!")

        # 3. Seed categories for demo user if none exist
        categories = (
            db.execute(select(Category).where(Category.user_id == demo_user.id))
            .scalars()
            .all()
        )
        cat_map = {c.name: c for c in categories}
        if not categories:
            default_cats = [
                ("Groceries", "shopping-cart", "#10b981"),
                ("Electronics", "laptop", "#3b82f6"),
                ("Home & Kitchen", "home", "#f59e0b"),
                ("Dining & Entertainment", "coffee", "#ec4899"),
                ("Utilities & Bills", "zap", "#8b5cf6"),
                ("Subscriptions", "repeat", "#6366f1"),
            ]
            for name, icon, color in default_cats:
                cat = Category(
                    user_id=demo_user.id,
                    name=name,
                    icon=icon,
                    color=color,
                    is_system=True,
                )
                db.add(cat)
                db.flush()
                cat_map[name] = cat
            print("  Created default categories.")

        # 4. Seed receipts if none exist
        receipt_count = (
            db.execute(select(Receipt).where(Receipt.user_id == demo_user.id))
            .scalars()
            .all()
        )
        if not receipt_count:
            now = datetime.now(timezone.utc)

            # Receipt 1: Apple Store
            r1 = Receipt(
                user_id=demo_user.id,
                category_id=cat_map.get("Electronics", {}).id
                if "Electronics" in cat_map
                else None,
                merchant_name="Apple Store Fifth Ave",
                purchase_date=now - timedelta(days=45),
                total_amount=Decimal("1299.00"),
                subtotal=Decimal("1199.00"),
                tax_amount=Decimal("100.00"),
                currency="USD",
                payment_method="APPLE PAY",
                receipt_number="APL-90421",
                notes="MacBook Air M3 purchase",
                status="CONFIRMED",
            )
            db.add(r1)
            db.flush()
            db.add(
                ReceiptItem(
                    receipt_id=r1.id,
                    description="MacBook Air 15-inch M3",
                    quantity=Decimal("1"),
                    unit_price=Decimal("1199.00"),
                    total_price=Decimal("1199.00"),
                )
            )

            # Link purchase and warranty
            p1 = Purchase(
                user_id=demo_user.id,
                receipt_id=r1.id,
                product_name="MacBook Air 15-inch M3",
                brand="Apple",
                model_number="MBA15-M3",
                serial_number="C02G89XYMD6R",
                purchase_date=r1.purchase_date,
                price=r1.total_amount,
            )
            db.add(p1)
            db.flush()

            w1 = Warranty(
                user_id=demo_user.id,
                purchase_id=p1.id,
                receipt_id=r1.id,
                provider="AppleCare+ Limited Warranty",
                duration_months=12,
                start_date=r1.purchase_date,
                end_date=add_months(r1.purchase_date, 12),
                policy_number="AC-9941203",
                terms="Covers hardware defects and battery health below 80%.",
                status=calculate_warranty_status(add_months(r1.purchase_date, 12)),
            )
            db.add(w1)

            # Receipt 2: Organic Market (Expiring warranty demo item or groceries)
            r2 = Receipt(
                user_id=demo_user.id,
                category_id=cat_map.get("Groceries", {}).id
                if "Groceries" in cat_map
                else None,
                merchant_name="Whole Foods Market",
                purchase_date=now - timedelta(days=3),
                total_amount=Decimal("84.50"),
                currency="USD",
                payment_method="VISA",
                receipt_number="WFM-33109",
                notes="Weekly organic groceries and pantry restock",
                status="CONFIRMED",
            )
            db.add(r2)
            db.flush()
            db.add(
                ReceiptItem(
                    receipt_id=r2.id,
                    description="Organic Almond Milk 64oz",
                    quantity=Decimal("2"),
                    unit_price=Decimal("4.50"),
                    total_price=Decimal("9.00"),
                )
            )
            db.add(
                ReceiptItem(
                    receipt_id=r2.id,
                    description="Fair Trade Coffee Beans 1kg",
                    quantity=Decimal("1"),
                    unit_price=Decimal("18.50"),
                    total_price=Decimal("18.50"),
                )
            )
            db.add(
                ReceiptItem(
                    receipt_id=r2.id,
                    description="Organic Honeycrisp Apples",
                    quantity=Decimal("3"),
                    unit_price=Decimal("4.00"),
                    total_price=Decimal("12.00"),
                )
            )

            # Warranty 2: Expiring Soon Monitor
            w2 = Warranty(
                user_id=demo_user.id,
                provider="Dell Premium Panel Guarantee",
                duration_months=36,
                start_date=now - timedelta(days=365 * 3 - 14),
                end_date=now + timedelta(days=14),  # Expiring in 14 days
                policy_number="DELL-U2723QE",
                terms="Zero bright dot guarantee and advanced exchange service.",
                status="EXPIRING_SOON",
            )
            db.add(w2)

            print("  Created sample receipts and warranties.")

        # 5. Seed subscriptions if none exist
        sub_count = (
            db.execute(select(Subscription).where(Subscription.user_id == demo_user.id))
            .scalars()
            .all()
        )
        if not sub_count:
            now = datetime.now(timezone.utc)
            db.add(
                Subscription(
                    user_id=demo_user.id,
                    service_name="Netflix Premium",
                    billing_frequency="MONTHLY",
                    amount=Decimal("22.99"),
                    currency="USD",
                    status="ACTIVE",
                    start_date=now - timedelta(days=120),
                    next_renewal_date=now + timedelta(days=12),
                )
            )
            db.add(
                Subscription(
                    user_id=demo_user.id,
                    service_name="Spotify Family",
                    billing_frequency="MONTHLY",
                    amount=Decimal("16.99"),
                    currency="USD",
                    status="ACTIVE",
                    start_date=now - timedelta(days=200),
                    next_renewal_date=now + timedelta(days=5),
                )
            )
            db.add(
                Subscription(
                    user_id=demo_user.id,
                    service_name="GitHub Copilot",
                    billing_frequency="YEARLY",
                    amount=Decimal("100.00"),
                    currency="USD",
                    status="ACTIVE",
                    start_date=now - timedelta(days=60),
                    next_renewal_date=now + timedelta(days=305),
                )
            )
            db.add(
                Subscription(
                    user_id=demo_user.id,
                    service_name="Audible Premium Plus (Trial)",
                    billing_frequency="MONTHLY",
                    amount=Decimal("14.95"),
                    currency="USD",
                    status="TRIAL",
                    start_date=now - timedelta(days=28),
                    next_renewal_date=now + timedelta(hours=36),
                    trial_end_date=now + timedelta(hours=36),
                )
            )
            print("  Created sample subscriptions.")

        # 6. Seed Household & Split if none exist
        h_count = (
            db.execute(select(Household).where(Household.created_by == demo_user.id))
            .scalars()
            .all()
        )
        if not h_count:
            household = Household(
                name="Maple Street Apartment", created_by=demo_user.id
            )
            db.add(household)
            db.flush()
            db.add(
                HouseholdMember(
                    household_id=household.id, user_id=demo_user.id, role="OWNER"
                )
            )
            db.add(
                HouseholdMember(
                    household_id=household.id, user_id=alice_user.id, role="MEMBER"
                )
            )
            db.flush()

            # Equal split of $120.50 utility bill
            shares = [
                {"user_id": str(demo_user.id), "share_amount": "60.25"},
                {"user_id": str(alice_user.id), "share_amount": "60.25"},
            ]
            db.add(
                ExpenseSplit(
                    household_id=household.id,
                    paid_by=demo_user.id,
                    description="High-Speed Fiber Internet & Electricity",
                    split_type="EQUAL",
                    shares_data=json.dumps(shares),
                    total_amount=Decimal("120.50"),
                    currency="USD",
                    is_settled=False,
                )
            )
            print("  Created sample household and expense split.")

        # 7. Seed Notifications
        n_count = (
            db.execute(select(Notification).where(Notification.user_id == demo_user.id))
            .scalars()
            .all()
        )
        if not n_count:
            now = datetime.now(timezone.utc)
            db.add(
                Notification(
                    user_id=demo_user.id,
                    title="Warranty Expiring in 14 Days",
                    message="Your Dell Premium Panel Guarantee for monitor expires in 14 days.",
                    notification_type="WARRANTY",
                    deduplication_key=f"seed:warranty:dell:{now.strftime('%Y%m%d')}",
                    is_read=False,
                )
            )
            db.add(
                Notification(
                    user_id=demo_user.id,
                    title="Free Trial Expiring in 36 Hours",
                    message="Your Audible Premium Plus free trial will renew automatically.",
                    notification_type="TRIAL",
                    deduplication_key=f"seed:trial:audible:{now.strftime('%Y%m%d')}",
                    is_read=False,
                )
            )
            print("  Created sample notifications.")

        db.commit()
        print("==> Database seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
