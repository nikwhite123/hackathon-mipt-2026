import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

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


@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_predict_accepts_valid_format_and_returns_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/predict", json=PREDICT_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 1
    assert body["predicted_attack_method"] == "brute_force"
    assert body["predicted_target_object"] == "vpn_gateway"
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) >= 2
    assert "generated_at" in body
    assert "rationale" in body
    assert len(body["rationale"]) >= 3


@pytest.mark.asyncio
async def test_predict_recommendations_contains_password_policy_and_2fa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/predict/recommendations", json=PREDICT_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    titles = {item["title"] for item in body["recommendations"]}
    assert body["predicted_attack_method"] == "brute_force"
    assert "Настроить политику паролей" in titles
    assert "Включить 2FA" in titles


@pytest.mark.asyncio
async def test_stats_returns_real_aggregations_for_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_incidents"] == 2000
    assert len(body["incidents_by_hour"]) == 24
    assert len(body["incidents_by_region"]) >= 1
    assert len(body["incidents_by_target_object"]) >= 1


@pytest.mark.asyncio
async def test_threats_filter_by_severity():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/threats", params={"severity": "critical"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["threat_id"] == "TH-002"


@pytest.mark.asyncio
async def test_vulnerability_mapping_by_cve_like_payload():
    payload = {
        "vulnerabilities": [
            {
                "asset_id": "asset-1",
                "asset_name": "Corporate VPN",
                "asset_type": "vpn_gateway",
                "vulnerability_code": "CVE-2024-0001",
                "title": "Weak password policy and missing MFA",
                "severity": "high",
                "description": "VPN login is protected by weak password without MFA and lockout policy.",
            }
        ]
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/vulnerabilities/map", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 1
    assert body["items"][0]["matches"][0]["threat"]["threat_id"] == "TH-003"


@pytest.mark.asyncio
async def test_validation_error_for_hour():
    invalid_payload = {**PREDICT_PAYLOAD, "hour": 24}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/predict", json=invalid_payload)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Validation error"
    assert isinstance(body["errors"], list)


@pytest.mark.asyncio
async def test_validation_error_for_missing_required_field():
    invalid_payload = {key: value for key, value in PREDICT_PAYLOAD.items() if key != "organization_id"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/predict", json=invalid_payload)

    assert response.status_code == 422
    assert response.json()["detail"] == "Validation error"
