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


_counter = 0


async def register_and_login(client: AsyncClient):
    global _counter
    _counter += 1
    organizations = await client.get('/auth/organizations')
    assert organizations.status_code == 200
    organization_id = organizations.json()[0]['id']
    organization_code = organizations.json()[0]['code']

    register_payload = {
        'first_name': 'Ivan',
        'last_name': 'Petrov',
        'email': f'ivan{_counter}@example.com',
        'password': 'secret123',
        'organization_id': organization_id,
    }
    register_response = await client.post('/auth/register', json=register_payload)
    assert register_response.status_code == 200

    login_response = await client.post('/auth/login', json={'email': f'ivan{_counter}@example.com', 'password': 'secret123'})
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
async def test_swagger_oauth_token_endpoint_accepts_form_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        organizations = await client.get('/auth/organizations')
        organization_id = organizations.json()[0]['id']
        await client.post('/auth/register', json={
            'first_name': 'Swagger',
            'last_name': 'User',
            'email': 'swagger@example.com',
            'password': 'secret123',
            'organization_id': organization_id,
        })
        response = await client.post('/auth/token', data={'username': 'swagger@example.com', 'password': 'secret123'})

    assert response.status_code == 200
    assert response.json()['token_type'] == 'bearer'
    assert response.json()['access_token']
