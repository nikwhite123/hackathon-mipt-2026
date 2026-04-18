"""HTTP integration tests for auth, predictions, stats, org settings, and vulnerability mapping."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.dependencies import get_ml_prediction_model_service
from app.db.session import SessionLocal
from app.main import app
from app.models.organization import Organization
from app.models.user import User
from app.services.ml_prediction_model_service import MlPredictionResult

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


_counter = 0
TEST_PASSWORD = 'Secret12345'


def first_seeded_organization_code() -> str:
    """Return the code of the first organization row after bootstrap (deterministic seed)."""
    with SessionLocal() as db:
        row = db.query(Organization).order_by(Organization.id.asc()).first()
        assert row is not None and row.code is not None
        return str(row.code)


async def register_and_login(client: AsyncClient):
    """Register a unique user against a seeded org and return auth headers plus organization code."""
    global _counter
    _counter += 1
    seeded_code = first_seeded_organization_code()
    org_lookup = await client.get('/auth/organization/by-code', params={'code': seeded_code})
    assert org_lookup.status_code == 200
    organization_code = org_lookup.json()['code']

    register_payload = {
        'first_name': 'Ivan',
        'last_name': 'Petrov',
        'email': f'ivan{_counter}@example.com',
        'password': TEST_PASSWORD,
        'organization_code': organization_code,
    }
    register_response = await client.post('/auth/register', json=register_payload)
    assert register_response.status_code == 200

    login_response = await client.post(
        '/auth/login', json={'email': f'ivan{_counter}@example.com', 'password': TEST_PASSWORD}
    )
    assert login_response.status_code == 200
    token = login_response.json()['access_token']
    return {'Authorization': f'Bearer {token}'}, organization_code


@pytest.mark.asyncio
async def test_healthcheck():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_register_login_and_me():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        headers, _ = await register_and_login(client)
        me = await client.get('/auth/me', headers=headers)

    assert me.status_code == 200
    assert me.json()['email'].startswith('ivan')


@pytest.mark.asyncio
async def test_predict_accepts_valid_format_and_returns_schema():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        response = await client.post('/predict', json={**PREDICT_PAYLOAD, 'organization_id': organization_code}, headers=headers)

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
async def test_predict_keeps_heuristic_method_and_target_without_ml_request(monkeypatch: pytest.MonkeyPatch):
    service = get_ml_prediction_model_service()
    calls = {"count": 0}

    def fake_predict(payload, db=None):
        calls["count"] += 1
        return MlPredictionResult(
            attack_method="ransomware",
            target_object="file_server",
            confidence=0.99,
            rationale=["patched ml rationale"],
        )

    monkeypatch.setattr(service, "predict", fake_predict)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        response = await client.post("/predict", json={**PREDICT_PAYLOAD, "organization_id": organization_code}, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["predicted_attack_method"] == "brute_force"
    assert body["predicted_target_object"] == "vpn_gateway"
    assert calls["count"] == 0
    assert "patched ml rationale" not in body["rationale"]


@pytest.mark.asyncio
async def test_predict_uses_ml_method_and_target_only_when_requested(monkeypatch: pytest.MonkeyPatch):
    service = get_ml_prediction_model_service()

    def fake_predict(payload, db=None):
        return MlPredictionResult(
            attack_method="ransomware",
            target_object="file_server",
            confidence=0.91,
            rationale=["patched ml rationale"],
        )

    monkeypatch.setattr(service, "predict", fake_predict)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        base_payload = {**PREDICT_PAYLOAD, "organization_id": organization_code}
        heuristic_response = await client.post("/predict", json=base_payload, headers=headers)
        ml_response = await client.post("/predict", json={**base_payload, "prefer_ml": True}, headers=headers)

    assert heuristic_response.status_code == 200
    assert ml_response.status_code == 200
    heuristic = heuristic_response.json()
    ml = ml_response.json()
    assert heuristic["predicted_attack_method"] == "brute_force"
    assert heuristic["predicted_target_object"] == "vpn_gateway"
    assert ml["predicted_attack_method"] == "ransomware"
    assert ml["predicted_target_object"] == "file_server"
    assert ml["risk_score"] == heuristic["risk_score"]
    assert ml["predicted_attack_time_window"] == heuristic["predicted_attack_time_window"]
    assert ml["confidence"] == 0.91
    assert any("ML mode is active" in item for item in ml["rationale"])
    assert "patched ml rationale" in ml["rationale"]


@pytest.mark.asyncio
async def test_predict_recommendations_contains_password_policy_and_2fa():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        response = await client.post(
            "/predict/recommendations",
            json={**PREDICT_PAYLOAD, "organization_id": organization_code},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    titles = {item["title"] for item in body["recommendations"]}
    assert body["predicted_attack_method"] == "brute_force"
    assert "Настроить политику паролей" in titles
    assert "Включить 2FA" in titles


@pytest.mark.asyncio
async def test_stats_returns_organization_filtered_aggregations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login(client)
        response = await client.get("/stats", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_incidents"] >= 1
    assert len(body["incidents_by_hour"]) >= 1
    assert len(body["incidents_by_region"]) >= 1
    assert len(body["incidents_by_target_object"]) >= 1
    assert "incidents_by_month" in body
    assert "incidents_by_attack_method" in body
    assert isinstance(body["incidents_by_attack_method"], dict)


@pytest.mark.asyncio
async def test_stats_rejects_missing_user_organization():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login(client)

    organization_id: int
    original_code: str | None
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == f"ivan{_counter}@example.com").first()
        assert user is not None
        organization = db.query(Organization).filter(Organization.id == user.organization_id).first()
        assert organization is not None
        organization_id = organization.id
        original_code = organization.code
        db.execute(update(Organization).where(Organization.id == organization_id).values(code=None))
        db.commit()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/stats", headers=headers)
    finally:
        with SessionLocal() as db:
            db.execute(update(Organization).where(Organization.id == organization_id).values(code=original_code))
            db.commit()

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is unavailable"


@pytest.mark.asyncio
async def test_stats_optional_filters():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login(client)
        r_all = await client.get("/stats", headers=headers)
        r_winter = await client.get("/stats", headers=headers, params={"season": "winter"})
        r_malware = await client.get("/stats", headers=headers, params={"attack_method": "malware"})
    assert r_all.status_code == 200
    assert r_winter.status_code == 200
    assert r_malware.status_code == 200
    body_w = r_winter.json()
    assert body_w["total_incidents"] <= r_all.json()["total_incidents"]


@pytest.mark.asyncio
async def test_stats_facets_for_organization():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login(client)
        response = await client.get("/stats/facets", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "regions" in body and "industries" in body
    assert isinstance(body["regions"], list)
    assert isinstance(body["industries"], list)


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
        headers, _ = await register_and_login(client)
        response = await client.post("/vulnerabilities/map", json=payload, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 1
    assert body["items"][0]["matches"][0]["threat"]["threat_id"] == "TH-003"


@pytest.mark.asyncio
async def test_forbidden_for_another_organization():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        headers, organization_code = await register_and_login(client)
        wrong_code = '999999'
        assert wrong_code != organization_code
        response = await client.post('/predict', json={**PREDICT_PAYLOAD, 'organization_id': wrong_code}, headers=headers)

    assert response.status_code == 403
    assert response.json()['detail'] == 'Access to another organization is forbidden'


@pytest.mark.asyncio
async def test_validation_error_for_hour():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        invalid_payload = {**PREDICT_PAYLOAD, "hour": 24, "organization_id": organization_code}
        response = await client.post("/predict", json=invalid_payload, headers=headers)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Validation error"
    assert isinstance(body["errors"], list)


@pytest.mark.asyncio
async def test_predict_time_target_method_endpoints_match_full_predict():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login(client)
        base = {**PREDICT_PAYLOAD, "organization_id": organization_code}
        full = await client.post("/predict", json=base, headers=headers)
        t_time = await client.post("/predict/time", json=base, headers=headers)
        t_target = await client.post("/predict/target", json=base, headers=headers)
        t_method = await client.post("/predict/method", json=base, headers=headers)

    assert full.status_code == 200
    assert t_time.status_code == 200
    assert t_target.status_code == 200
    assert t_method.status_code == 200
    body = full.json()
    assert t_time.json()["predicted_attack_time_window"] == body["predicted_attack_time_window"]
    assert t_target.json()["predicted_target_object"] == body["predicted_target_object"]
    assert t_method.json()["predicted_attack_method"] == body["predicted_attack_method"]


@pytest.mark.asyncio
async def test_organization_settings_get_null_then_upsert():
    settings_payload = {
        "region": "Moscow",
        "industry": "telecom",
        "host_count": 50,
        "technologies": ["nginx", "postgres"],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login(client)
        r0 = await client.get("/org/settings", headers=headers)
        assert r0.status_code == 200
        assert r0.json() is None
        r1 = await client.post("/org/settings", json=settings_payload, headers=headers)
        assert r1.status_code == 200
        r2 = await client.get("/org/settings", headers=headers)

    saved = r2.json()
    assert saved["region"] == settings_payload["region"]
    assert saved["industry"] == settings_payload["industry"]
    assert saved["host_count"] == settings_payload["host_count"]
    assert saved["technologies"] == settings_payload["technologies"]


@pytest.mark.asyncio
async def test_predict_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/predict", json=PREDICT_PAYLOAD)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_threats_list_returns_items():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/threats")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert "threat_id" in body["items"][0]


@pytest.mark.asyncio
async def test_swagger_oauth_token_endpoint_accepts_form_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        await client.post('/auth/register', json={
            'first_name': 'Swagger',
            'last_name': 'User',
            'email': 'swagger@example.com',
            'password': TEST_PASSWORD,
            'organization_code': first_seeded_organization_code(),
        })
        response = await client.post('/auth/token', data={'username': 'swagger@example.com', 'password': TEST_PASSWORD})

    assert response.status_code == 200
    assert response.json()['token_type'] == 'bearer'
    assert response.json()['access_token']
