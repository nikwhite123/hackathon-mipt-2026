from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

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
    "known_vulnerabilities_count": 4,
}


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_full_response():
    response = client.post("/predict", json=PREDICT_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_attack_time_window"] == "06:00-12:00"
    assert body["predicted_target_object"] == "vpn_gateway"
    assert body["predicted_attack_method"] == "brute_force"
    assert len(body["recommendations"]) >= 1


def test_predict_time_response():
    response = client.post("/predict/time", json=PREDICT_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["predicted_attack_time_window"] == "06:00-12:00"


def test_predict_target_response():
    response = client.post("/predict/target", json=PREDICT_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["predicted_target_object"] == "vpn_gateway"


def test_predict_method_response():
    response = client.post("/predict/method", json=PREDICT_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["predicted_attack_method"] == "brute_force"


def test_predict_recommendations_response():
    response = client.post("/predict/recommendations", json=PREDICT_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["predicted_attack_method"] == "brute_force"
    assert len(body["recommendations"]) >= 1


def test_threats_filter_by_severity():
    response = client.get("/threats", params={"severity": "critical"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["threat_id"] == "TH-002"


def test_vulnerability_mapping():
    payload = {
        "vulnerabilities": [
            {
                "asset_id": "asset-1",
                "asset_name": "Corporate VPN",
                "asset_type": "vpn_gateway",
                "vulnerability_code": "CWE-307",
                "title": "Weak password policy",
                "severity": "high",
                "description": "VPN login is protected by weak password without MFA",
            }
        ]
    }
    response = client.post("/vulnerabilities/map", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 1
    assert body["items"][0]["matches"][0]["threat"]["threat_id"] == "TH-003"


def test_validation_error_for_hour():
    invalid_payload = {**PREDICT_PAYLOAD, "hour": 24}
    response = client.post("/predict", json=invalid_payload)
    assert response.status_code == 422
    assert response.json()["detail"] == "Validation error"
