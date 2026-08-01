#!/usr/bin/env python3
"""
Initialize the database with an admin user.
Run once: python init_db.py
"""
from app.db.base import Base, engine, SessionLocal
from app.models.customer import Customer
from app.core.security import generate_api_key, hash_api_key

def init():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Check if admin exists
    admin = db.query(Customer).filter(Customer.is_admin == True).first()
    if admin:
        print(f"Admin already exists: {admin.email}")
        return

    # Create default admin
    api_key = generate_api_key()
    hashed = hash_api_key(api_key)

    admin = Customer(
        email="admin@roamwise.co.in",
        company_name="RoamWise",
        hashed_api_key=hashed,
        tier="enterprise",
        is_active=True,
        is_admin=True,
        monthly_quota=999999,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print("=" * 60)
    print("ROAMWISE DEVELOPER API - ADMIN CREATED")
    print("=" * 60)
    print(f"Email: admin@roamwise.co.in")
    print(f"API Key: {api_key}")
    print("=" * 60)
    print("WARNING: Store this key safely. It will not be shown again.")
    print("=" * 60)

if __name__ == "__main__":
    init()
