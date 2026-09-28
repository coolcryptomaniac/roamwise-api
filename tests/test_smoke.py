"""
Smoke tests: does the app boot and does every documented endpoint actually
work end-to-end, not just import cleanly? This is what CI runs on every
push — it's what would have caught main.py importing seven router modules
that didn't exist, before that ever reached a deploy.
"""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "operational"


def test_pricing_is_public(client):
    r = client.get("/v1/pricing")
    assert r.status_code == 200
    assert len(r.json()["tiers"]) == 3


def test_protected_endpoint_requires_key(client):
    r = client.post("/v1/budget/calculate", json={"destination": "Goa", "duration_days": 3, "travelers": 2})
    assert r.status_code == 401


def test_budget_calculate(client, api_key):
    r = client.post(
        "/v1/budget/calculate",
        headers={"X-API-Key": api_key},
        json={"destination": "Goa", "duration_days": 3, "travelers": 2, "tier": "mid"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_inr"] > 0
    assert body["total_inr"] == sum(body["breakdown_inr"].values())


def test_packing_list(client, api_key):
    r = client.post(
        "/v1/packing/list",
        headers={"X-API-Key": api_key},
        json={"destination": "Manali", "duration_days": 5, "climate": "cold", "activities": ["trekking"]},
    )
    assert r.status_code == 200
    items = r.json()["items"]
    assert "Trekking shoes" in items
    assert "Thermal layers" in items


def test_visa_guide_known_pair(client, api_key):
    r = client.post(
        "/v1/visa/guide",
        headers={"X-API-Key": api_key},
        json={"nationality": "IN", "destination_country": "TH"},
    )
    assert r.status_code == 200
    assert r.json()["visa_required"] is False


def test_visa_guide_unknown_pair_is_honest_not_fabricated(client, api_key):
    r = client.post(
        "/v1/visa/guide",
        headers={"X-API-Key": api_key},
        json={"nationality": "XX", "destination_country": "YY"},
    )
    assert r.status_code == 200
    assert r.json()["covered"] is False


def test_itinerary_generate(client, api_key):
    r = client.post(
        "/v1/itinerary/generate",
        headers={"X-API-Key": api_key},
        json={"destination": "Manali", "duration_days": 4, "travelers": 2},
    )
    assert r.status_code == 200
    days = r.json()["days"]
    assert len(days) == 4
    assert days[0]["label"] == "Arrival"
    assert days[-1]["label"] == "Departure"


def test_crowd_forecast_refuses_instead_of_fabricating(client, api_key):
    r = client.post(
        "/v1/crowd/forecast",
        headers={"X-API-Key": api_key},
        json={"destination": "Manali", "date": "2026-10-01"},
    )
    assert r.status_code == 501


def test_usage_stats_reflect_real_calls(client, api_key):
    client.post(
        "/v1/budget/calculate",
        headers={"X-API-Key": api_key},
        json={"destination": "Goa", "duration_days": 1, "travelers": 1},
    )
    r = client.get("/v1/usage/stats", headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["requests_used_this_month"] >= 1


def test_admin_can_create_customer(client, admin_api_key):
    r = client.post(
        "/v1/admin/customers",
        headers={"X-API-Key": admin_api_key},
        json={"email": "new-customer@example.com", "tier": "pro"},
    )
    assert r.status_code == 201
    assert r.json()["api_key"].startswith("rw_live_")


def test_non_admin_cannot_create_customer(client, api_key):
    r = client.post(
        "/v1/admin/customers",
        headers={"X-API-Key": api_key},
        json={"email": "someone-else@example.com", "tier": "basic"},
    )
    assert r.status_code == 403
