"""Monthly quota must reset when the month changes.

Before this fix requests_used_this_month only ever grew, so a customer on
"1,000 requests/month" was locked out permanently after their first 1,000 calls.
"""
from datetime import datetime, timezone

from app.core.security import hash_api_key
from app.db.session import SessionLocal
from app.dependencies import current_quota_period, roll_monthly_quota
from app.models.customer import Customer


def _set(api_key, **fields):
    db = SessionLocal()
    try:
        c = db.query(Customer).filter(Customer.hashed_api_key == hash_api_key(api_key)).first()
        for k, v in fields.items():
            setattr(c, k, v)
        db.commit()
    finally:
        db.close()


def _usage(client, api_key):
    r = client.get("/v1/usage/stats", headers={"X-API-Key": api_key})
    return r


def test_quota_exhausted_in_current_month_is_still_blocked(client, api_key):
    _set(api_key, requests_used_this_month=1000, quota_period=current_quota_period())
    assert _usage(client, api_key).status_code == 429


def test_quota_from_a_previous_month_resets(client, api_key):
    _set(api_key, requests_used_this_month=1000, quota_period="2020-01")
    r = _usage(client, api_key)
    assert r.status_code == 200
    assert r.json()["requests_used_this_month"] == 0
    assert r.json()["requests_remaining"] == 1000


def test_legacy_customer_without_period_is_not_locked_out(client, api_key):
    _set(api_key, requests_used_this_month=1000, quota_period=None)
    assert _usage(client, api_key).status_code == 200


def test_roll_is_a_no_op_within_the_same_month():
    db = SessionLocal()
    try:
        c = Customer(email="roll@example.com", hashed_api_key="x-roll", requests_used_this_month=7, quota_period="2026-11")
        db.add(c)
        db.commit()
        roll_monthly_quota(c, db, now=datetime(2026, 11, 30, 23, 59, tzinfo=timezone.utc))
        assert c.requests_used_this_month == 7
        roll_monthly_quota(c, db, now=datetime(2026, 12, 1, 0, 0, tzinfo=timezone.utc))
        assert (c.requests_used_this_month, c.quota_period) == (0, "2026-12")
    finally:
        db.close()
