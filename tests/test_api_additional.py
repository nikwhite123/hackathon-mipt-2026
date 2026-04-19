"""Additional integration tests to cover remaining API routes and negative scenarios."""

from __future__ import annotations

import itertools

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import SessionLocal
from app.main import app
from app.models.organization import Organization

_counter = itertools.count(1000)
TEST_PASSWORD = "Secret12345"
PREDICT_PAYLOAD = {
    "organization_id": "org-001",
    "region": "Moscow",
    "industry": "telecom",
    "season": "winter",
    "day_of_week": 2,
    "hour": 9,
    "asset_type": "vpn_gateway",
    "has_external_access": True,
    "privileged_accounts_count": 12,
    "known_vulnerabilities_count": 3,
}


def first_seeded_organization_code() -> str:
    with SessionLocal() as db:
        row = db.query(Organization).order_by(Organization.id.asc()).first()
        assert row is not None and row.code is not None
        return str(row.code)


async def register_and_login(client: AsyncClient) -> tuple[dict[str, str], str, str]:
    idx = next(_counter)
    organization_code = first_seeded_organization_code()
    email = f"extra{idx}@example.com"
    register_payload = {
        "first_name": "Petr",
        "last_name": "Sidorov",
        "email": email,
        "password": TEST_PASSWORD,
        "organization_code": organization_code,
    }
    response = await client.post("/auth/register", json=register_payload)
    assert response.status_code == 200
    login = await client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, organization_code, email


@pytest.mark.asyncio
async def test_auth_organization_by_code_returns_404_for_unknown_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth/organization/by-code", params={"code": "missing-org"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        organization_code = first_seeded_organization_code()
        payload = {
            "first_name": "Anna",
            "last_name": "Ivanova",
            "email": f"dup{next(_counter)}@example.com",
            "password": TEST_PASSWORD,
            "organization_code": organization_code,
        }
        first = await client.post("/auth/register", json=payload)
        second = await client.post("/auth/register", json=payload)
    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "User with this email already exists"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        organization_code = first_seeded_organization_code()
        email = f"wrongpass{next(_counter)}@example.com"
        payload = {
            "first_name": "Oleg",
            "last_name": "Fedorov",
            "email": email,
            "password": TEST_PASSWORD,
            "organization_code": organization_code,
        }
        register = await client.post("/auth/register", json=payload)
        assert register.status_code == 200
        login = await client.post("/auth/login", json={"email": email, "password": "BadPassword123"})
    assert login.status_code == 401
    assert login.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_oauth_token_endpoint_returns_bearer_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        organization_code = first_seeded_organization_code()
        email = f"oauth{next(_counter)}@example.com"
        register = await client.post(
            "/auth/register",
            json={
                "first_name": "Lev",
                "last_name": "Popov",
                "email": email,
                "password": TEST_PASSWORD,
                "organization_code": organization_code,
            },
        )
        assert register.status_code == 200
        token = await client.post(
            "/auth/token",
            data={"username": email, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    assert token.status_code == 200
    body = token.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_predict_subroutes_return_expected_slices():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code, _ = await register_and_login(client)
        payload = {**PREDICT_PAYLOAD, "organization_id": organization_code}
        time_response = await client.post("/predict/time", json=payload, headers=headers)
        target_response = await client.post("/predict/target", json=payload, headers=headers)
        method_response = await client.post("/predict/method", json=payload, headers=headers)

    assert time_response.status_code == 200
    assert target_response.status_code == 200
    assert method_response.status_code == 200

    time_body = time_response.json()
    target_body = target_response.json()
    method_body = method_response.json()

    assert time_body["predicted_attack_time_window"]
    assert 0 <= time_body["confidence"] <= 1
    assert target_body["predicted_target_object"] == "vpn_gateway"
    assert method_body["predicted_attack_method"] == "brute_force"


@pytest.mark.asyncio
async def test_predict_forbids_access_to_another_organization():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code, _ = await register_and_login(client)
        assert organization_code != "org-999"
        response = await client.post(
            "/predict",
            json={**PREDICT_PAYLOAD, "organization_id": "org-999"},
            headers=headers,
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access to another organization is forbidden"


@pytest.mark.asyncio
async def test_org_settings_lifecycle_create_and_read():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _, _ = await register_and_login(client)
        before = await client.get("/org/settings", headers=headers)
        create = await client.post(
            "/org/settings",
            json={
                "region": "Moscow",
                "industry": "telecom",
                "host_count": 250,
                "technologies": ["nginx", "postgres", "kafka"],
            },
            headers=headers,
        )
        after = await client.get("/org/settings", headers=headers)

    assert before.status_code == 200
    assert create.status_code == 200
    assert after.status_code == 200
    body = after.json()
    assert body["region"] == "Moscow"
    assert body["industry"] == "telecom"
    assert body["host_count"] == 250
    assert body["technologies"] == ["nginx", "postgres", "kafka"]


@pytest.mark.asyncio
async def test_threats_support_severity_and_category_filters():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        critical = await client.get("/threats", params={"severity": "critical"})
        app_attack = await client.get("/threats", params={"category": "application_attack"})

    assert critical.status_code == 200
    assert app_attack.status_code == 200
    critical_body = critical.json()
    app_attack_body = app_attack.json()
    assert critical_body["total"] >= 1
    assert all(item["severity"] == "critical" for item in critical_body["items"])
    assert app_attack_body["total"] >= 1
    assert all(item["category"] == "application_attack" for item in app_attack_body["items"])


@pytest.mark.asyncio
async def test_vulnerability_mapping_returns_specific_and_fallback_matches():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _, _ = await register_and_login(client)
        response = await client.post(
            "/vulnerabilities/map",
            json={
                "vulnerabilities": [
                    {
                        "asset_id": "srv-1",
                        "asset_name": "VPN Gateway",
                        "asset_type": "vpn_gateway",
                        "vulnerability_code": "CVE-2026-0001",
                        "title": "Weak password policy on VPN login",
                        "severity": "high",
                        "description": "VPN auth without MFA and weak password checks",
                    },
                    {
                        "asset_id": "ws-1",
                        "asset_name": "Workstation #1",
                        "asset_type": "workstation",
                        "vulnerability_code": "GEN-2026-9999",
                        "title": "Suspicious malware loader",
                        "severity": "low",
                        "description": "Potential malware loader execution on workstation",
                    },
                ]
            },
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 2
    assert body["total_vulnerabilities"] == 2

    first_match = body["items"][0]["matches"][0]
    second_match = body["items"][1]["matches"][0]
    assert first_match["threat"]["threat_id"] == "TH-003"
    assert second_match["threat"]["threat_id"] == "TH-005"


@pytest.mark.asyncio
async def test_vulnerability_mapping_rejects_empty_payload():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _, _ = await register_and_login(client)
        response = await client.post("/vulnerabilities/map", json={"vulnerabilities": []}, headers=headers)
    assert response.status_code == 422
    assert response.json()["detail"] == "Validation error"
