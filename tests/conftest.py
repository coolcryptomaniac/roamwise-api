import os
import tempfile

# Settings/engine are read at import time (get_settings() is lru_cache'd),
# so env vars must be set before anything under app/ is imported anywhere,
# including by pytest's own collection of other test files.
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-not-a-real-secret")
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_db.name}")

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base, engine
from app.db.session import SessionLocal
from app.models.customer import Customer
from app.core.security import generate_api_key, hash_api_key


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def api_key():
    """A fresh, active basic-tier customer for each test that needs auth."""
    raw_key = generate_api_key()
    db = SessionLocal()
    try:
        customer = Customer(
            email=f"test-{raw_key[-8:]}@example.com",
            hashed_api_key=hash_api_key(raw_key),
            tier="basic",
            is_active=True,
            is_admin=False,
            monthly_quota=1000,
        )
        db.add(customer)
        db.commit()
    finally:
        db.close()
    return raw_key


@pytest.fixture()
def admin_api_key():
    raw_key = generate_api_key()
    db = SessionLocal()
    try:
        customer = Customer(
            email=f"admin-{raw_key[-8:]}@example.com",
            hashed_api_key=hash_api_key(raw_key),
            tier="enterprise",
            is_active=True,
            is_admin=True,
            monthly_quota=999999,
        )
        db.add(customer)
        db.commit()
    finally:
        db.close()
    return raw_key
