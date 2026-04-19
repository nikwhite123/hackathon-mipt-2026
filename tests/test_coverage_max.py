from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pandas as pd
import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import get_current_user
from app.auth.security import create_access_token, decode_token
from app.core.settings import settings
from app.main import app
from app.processors.scoring import ThreatScoringProcessor
from app.repositories.config_repository import ConfigRepository
from app.schemas import (
    InfrastructureVulnerability,
    LoginRequest,
    OrganizationSettingsRequest,
    PredictRequest,
    RuleConfig,
    UserRegisterRequest,
    VulnerabilityMapRequest,
)
from app.services.access_control_service import AccessControlService
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthService
from app.services.organization_settings_service import OrganizationSettingsService
from app.services.prediction_service import PredictionService
from app.services.risk_context_service import RiskContextService
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService
from app.strategies.vulnerability_mapping import RuleBasedThreatMatchingStrategy, VulnerabilityTextIndex
from tests.test_api import TEST_PASSWORD, first_seeded_organization_code


_auth_counter = 10000


async def register_and_login_unique(client: AsyncClient):
    global _auth_counter
    _auth_counter += 1
    email = f"coverage{_auth_counter}@example.com"
    code = first_seeded_organization_code()
    register_payload = {
        "first_name": "Ivan",
        "last_name": "Petrov",
        "email": email,
        "password": TEST_PASSWORD,
        "organization_code": code,
    }
    register_response = await client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 200, register_response.text
    login_response = await client.post("/auth/login", json={"email": email, "password": TEST_PASSWORD})
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, code


class FakeRiskContextService:
    def __init__(self, intensity: float):
        self.intensity = intensity

    def get_attack_intensity(self, **kwargs):
        return self.intensity


class FakeMlService:
    def __init__(self, result):
        self.result = result

    def predict(self, payload, db=None):
        return self.result


class FakeThreatCatalog:
    def __init__(self):
        self.service = ThreatCatalogService(ConfigRepository())

    def get_recommendations(self, method: str):
        return self.service.get_recommendations(method)

    def get_threat_by_id(self, threat_id: str):
        return self.service.get_threat_by_id(threat_id)


class DummyRepo:
    def __init__(self, incidents: pd.DataFrame, registry: pd.DataFrame | None = None):
        self._incidents = incidents
        self._registry = registry if registry is not None else pd.DataFrame()
        self.load_calls: list[tuple[str, object]] = []

    def load_incidents_by_organization_code(self, organization_code, db=None, incident_filters=None):
        self.load_calls.append(("by_org", incident_filters))
        return self._incidents.copy()

    def load_incidents(self, db=None):
        self.load_calls.append(("all", None))
        return self._incidents.copy()

    def load_fstec_registry(self, db=None):
        return self._registry.copy()

    def distinct_incident_facets(self, organization_code, db):
        return ["Moscow", "Perm"], ["telecom", "finance"]


class FakeAuthRepository:
    def __init__(self, *, user=None, organization=None, organization_by_code=None):
        self.user = user
        self.organization = organization
        self.organization_by_code = organization_by_code
        self.created_user_kwargs = None

    def get_user_by_email(self, email):
        return self.user

    def get_organization_by_code(self, code):
        return self.organization_by_code

    def create_user(self, **kwargs):
        self.created_user_kwargs = kwargs
        return SimpleNamespace(id=7, **kwargs)

    def get_organization(self, organization_id):
        return self.organization


@pytest.mark.asyncio
async def test_empty_vulnerability_list_now_returns_422_and_not_500():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login_unique(client)
        response = await client.post("/vulnerabilities/map", json={"vulnerabilities": []}, headers=headers)

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Validation error"
    assert body["code"] == "validation_error"
    assert any("At least one vulnerability is required" in str(err) for err in body["errors"])


@pytest.mark.asyncio
async def test_login_rejects_wrong_password_and_unknown_org_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        register = await client.post(
            "/auth/register",
            json={
                "first_name": "Petr",
                "last_name": "Ivanov",
                "email": "badpass@example.com",
                "password": TEST_PASSWORD,
                "organization_code": first_seeded_organization_code(),
            },
        )
        wrong_password = await client.post(
            "/auth/login", json={"email": "badpass@example.com", "password": "WrongPassword1"}
        )
        missing_org = await client.get("/auth/organization/by-code", params={"code": "does-not-exist"})

    assert register.status_code == 200
    assert wrong_password.status_code == 401
    assert wrong_password.json()["detail"] == "Incorrect email or password"
    assert missing_org.status_code == 404


@pytest.mark.asyncio
async def test_register_duplicate_email_and_invalid_org_settings_are_rejected():
    email = "dup@example.com"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post(
            "/auth/register",
            json={
                "first_name": "Anna",
                "last_name": "Smirnova",
                "email": email,
                "password": TEST_PASSWORD,
                "organization_code": first_seeded_organization_code(),
            },
        )
        second = await client.post(
            "/auth/register",
            json={
                "first_name": "Anna",
                "last_name": "Smirnova",
                "email": email,
                "password": TEST_PASSWORD,
                "organization_code": first_seeded_organization_code(),
            },
        )
        headers, _ = await register_and_login_unique(client)
        bad_settings = await client.post(
            "/org/settings",
            headers=headers,
            json={"region": "Moscow", "industry": "telecom", "host_count": 0, "technologies": []},
        )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "User with this email already exists"
    assert bad_settings.status_code == 422


@pytest.mark.asyncio
async def test_auth_me_rejects_token_with_wrong_organization_claim():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/auth/register",
            json={
                "first_name": "Token",
                "last_name": "Mismatch",
                "email": "token-mismatch@example.com",
                "password": TEST_PASSWORD,
                "organization_code": first_seeded_organization_code(),
            },
        )
        bad_token = create_access_token(subject="token-mismatch@example.com", organization_id=999999)
        response = await client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_stats_filters_cover_success_time_of_day_date_range_and_threat_code():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, _ = await register_and_login_unique(client)
        response = await client.get(
            "/stats",
            headers=headers,
            params={
                "success": 1,
                "time_of_day": "morning",
                "date_from": "2026-01-01",
                "date_to": "2026-12-31",
                "threat_code": 101,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["total_incidents"] >= 0
    assert isinstance(body["risk_distribution"], dict)


def test_security_token_roundtrip_and_invalid_token():
    token = create_access_token(subject="alice@example.com", organization_id=42, expires_delta=timedelta(minutes=5))
    decoded = decode_token(token)

    assert decoded["sub"] == "alice@example.com"
    assert decoded["organization_id"] == 42

    with pytest.raises(ValueError):
        decode_token(token + "broken")


def test_access_control_service_rejects_missing_org_and_wrong_code():
    service = AccessControlService()
    payload = PredictRequest(
        organization_id="org-001",
        region="Moscow",
        industry="telecom",
        season="winter",
        day_of_week=1,
        hour=9,
        asset_type="vpn_gateway",
        has_external_access=True,
        privileged_accounts_count=10,
        known_vulnerabilities_count=3,
    )

    class QueryNone:
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return None

    class DummyDB:
        def query(self, model):
            return QueryNone()

    with pytest.raises(HTTPException) as missing:
        service.ensure_prediction_access(payload, SimpleNamespace(organization_id=1), DummyDB())
    assert missing.value.status_code == 403
    assert missing.value.detail == "User organization is not configured"

    class QueryOrg:
        def __init__(self, org):
            self.org = org
        def filter(self, *args, **kwargs):
            return self
        def first(self):
            return self.org

    class DummyDB2:
        def __init__(self, org):
            self.org = org
        def query(self, model):
            return QueryOrg(self.org)

    with pytest.raises(HTTPException) as wrong:
        service.ensure_prediction_access(payload, SimpleNamespace(organization_id=1), DummyDB2(SimpleNamespace(code="org-999")))
    assert wrong.value.status_code == 403
    assert wrong.value.detail == "Access to another organization is forbidden"

    assert (
        service.ensure_prediction_access(
            payload, SimpleNamespace(organization_id=1), DummyDB2(SimpleNamespace(code="org-001"))
        )
        == "org-001"
    )


def test_vulnerability_text_index_and_rule_strategy_match_and_no_match():
    vulnerability = InfrastructureVulnerability(
        asset_id="a1",
        asset_name="VPN",
        asset_type="vpn_gateway",
        vulnerability_code="CVE-2026-1234",
        title="Weak password policy",
        severity="high",
        description="Missing MFA on external login",
    )
    idx = VulnerabilityTextIndex.from_vulnerability(vulnerability)
    assert idx.contains_any(["weak", "other"])
    assert idx.contains_any(["*"])
    assert not idx.contains_any(["sql", "browser"])

    catalog = FakeThreatCatalog()
    rule = RuleConfig(
        threat_id="TH-003",
        tokens=["password", "mfa"],
        match_score=0.92,
        reason="Credential attack indicators found",
        recommendation_method="brute_force",
    )
    strategy = RuleBasedThreatMatchingStrategy(rule, catalog)
    match = strategy.match(vulnerability)
    assert match is not None
    assert match.threat.threat_id == "TH-003"
    assert match.match_score == 0.92

    miss_rule = RuleConfig(
        threat_id="TH-003",
        tokens=["sql"],
        match_score=0.5,
        reason="Nope",
        recommendation_method="brute_force",
    )
    assert RuleBasedThreatMatchingStrategy(miss_rule, catalog).match(vulnerability) is None


def test_vulnerability_mapping_service_deduplicates_sorts_and_uses_fallback():
    catalog = FakeThreatCatalog()
    vuln = InfrastructureVulnerability(
        asset_id="asset-1",
        asset_name="Server",
        asset_type="workstation",
        vulnerability_code="CVE-1",
        title="General malware issue",
        severity="medium",
        description="Malware suspicious code execution",
    )
    matched_rule_1 = RuleConfig(
        threat_id="TH-005",
        tokens=["malware"],
        match_score=0.7,
        reason="malware token",
        recommendation_method="malware",
    )
    matched_rule_2 = RuleConfig(
        threat_id="TH-005",
        tokens=["code"],
        match_score=0.9,
        reason="better malware token",
        recommendation_method="malware",
    )
    fallback_rule = RuleConfig(
        threat_id="TH-002",
        tokens=["*"],
        match_score=0.4,
        reason="fallback",
        recommendation_method="phishing",
    )
    service = VulnerabilityMappingService(
        [
            RuleBasedThreatMatchingStrategy(matched_rule_1, catalog),
            RuleBasedThreatMatchingStrategy(matched_rule_2, catalog),
        ],
        RuleBasedThreatMatchingStrategy(fallback_rule, catalog),
    )
    result = service.map_vulnerabilities(VulnerabilityMapRequest(vulnerabilities=[vuln]))
    assert result.total_assets == 1
    assert result.total_vulnerabilities == 1
    assert len(result.items[0].matches) == 1
    assert result.items[0].matches[0].match_score == 0.9

    unmatched = InfrastructureVulnerability(
        asset_id="asset-2",
        asset_name="Other",
        asset_type="crm",
        vulnerability_code="CVE-2",
        title="Unknown issue",
        severity="low",
        description="No known tokens here",
    )
    fallback_only = VulnerabilityMappingService([], RuleBasedThreatMatchingStrategy(fallback_rule, catalog))
    fallback_result = fallback_only.map_vulnerabilities(VulnerabilityMapRequest(vulnerabilities=[unmatched]))
    assert fallback_result.items[0].matches[0].threat.threat_id == "TH-002"


def test_threat_catalog_service_filters_and_get_threat_by_id_error():
    service = ThreatCatalogService(ConfigRepository())
    critical = service.list_threats(SimpleNamespace(severity="critical", category=None))
    phishing = service.get_recommendations("phishing")

    assert critical.total >= 1
    assert all(item.severity == "critical" for item in critical.items)
    assert len(phishing) >= 1
    assert service.get_threat_by_id("TH-001").threat_id == "TH-001"
    with pytest.raises(KeyError):
        service.get_threat_by_id("TH-404")


def test_risk_context_service_fallbacks_and_industry_narrowing():
    incidents = pd.DataFrame(
        [
            {"region": "Moscow", "season": "winter", "industry": "telecom", "hour": 9},
            {"region": "Moscow", "season": "winter", "industry": "telecom", "hour": 9},
            {"region": "Moscow", "season": "winter", "industry": "telecom", "hour": 10},
            {"region": "Perm", "season": "winter", "industry": "finance", "hour": 9},
        ]
    )
    service = RiskContextService(DummyRepo(incidents))
    intensity = service.get_attack_intensity("Moscow", 9, "winter", organization_code="org-001", industry="telecom")
    assert intensity == 1.33

    empty_repo_service = RiskContextService(DummyRepo(pd.DataFrame(columns=["region", "season", "industry", "hour"])))
    assert empty_repo_service.get_attack_intensity("Moscow", 9, "winter") == 0.0


def test_threat_scoring_processor_includes_exposure_and_privileged_rationale():
    config = ConfigRepository().load_scoring_config()
    processor = ThreatScoringProcessor(config, FakeRiskContextService(2.5))
    payload = PredictRequest(
        organization_id="org-001",
        region="Moscow",
        industry="telecom",
        season="winter",
        day_of_week=2,
        hour=9,
        asset_type="vpn_gateway",
        has_external_access=True,
        privileged_accounts_count=12,
        known_vulnerabilities_count=4,
    )
    result = processor.score(payload)
    assert 0 <= result.risk_score <= 0.99
    assert 0 <= result.confidence <= 0.98
    assert any("external exposure" in item for item in result.rationale)
    assert any("privileged accounts" in item for item in result.rationale)


def test_prediction_service_ml_unavailable_and_time_bucket_edges():
    config = ConfigRepository().load_scoring_config()
    processor = ThreatScoringProcessor(config, FakeRiskContextService(1.0))
    service = PredictionService(processor, FakeThreatCatalog(), FakeMlService(None))
    payload = PredictRequest(
        organization_id="org-001",
        region="Moscow",
        industry="telecom",
        season="winter",
        day_of_week=2,
        hour=18,
        asset_type="vpn_gateway",
        has_external_access=True,
        privileged_accounts_count=2,
        known_vulnerabilities_count=1,
        prefer_ml=True,
    )
    response = service.predict(payload)
    assert response.predicted_attack_time_window == "18:00-24:00"
    assert response.predicted_attack_method == "brute_force"
    assert any("model output was unavailable" in item for item in response.rationale)
    assert PredictionService._detect_time_bucket(0) == "00:00-06:00"
    assert PredictionService._detect_time_bucket(6) == "06:00-12:00"
    assert PredictionService._detect_time_bucket(12) == "12:00-18:00"
    assert PredictionService._detect_time_bucket(23) == "18:00-24:00"
    assert PredictionService._detect_attack_method("unknown-target") == "malware"


def test_analytics_service_empty_and_detection_helpers():
    empty_repo = DummyRepo(pd.DataFrame(columns=["threat_code"]), pd.DataFrame(columns=["threat_code", "name", "description", "object_of_impact"]))
    empty_stats = AnalyticsService(empty_repo).build_stats("org-001")
    assert empty_stats.total_incidents == 0

    service = AnalyticsService(empty_repo)
    phishing_row = {"name": "Почтовая атака", "description": "Фишинговое письмо", "object_of_impact": "Почта"}
    sql_row = {"name": "SQL attack", "description": "sql injection in web app", "object_of_impact": "СУБД"}
    workstation_row = {"name": "Threat", "description": "bios compromise", "object_of_impact": "рабочий компьютер", "success": 1, "host_count": 1500, "attack_method": "ransomware"}
    assert service._detect_attack_method(phishing_row) == "phishing"
    assert service._detect_attack_method(sql_row) == "sql_injection"
    assert service._detect_target_object(sql_row) == "db_server"
    assert service._detect_target_object(workstation_row) == "workstation"
    assert service._detect_risk_level(workstation_row) == "critical"
    assert service._normalize_text("A", None, "nan", "B") == "a b"


def test_stats_service_passes_filters_only_when_present_and_facets_delegate():
    repo = DummyRepo(pd.DataFrame(columns=["threat_code"]))
    service = StatsService(repo)
    captured = {}

    def fake_build_stats(organization_code, incident_filters=None, attack_method=None, db=None):
        captured["organization_code"] = organization_code
        captured["incident_filters"] = incident_filters
        captured["attack_method"] = attack_method
        return "OK"

    service.analytics_service.build_stats = fake_build_stats
    result = service.build_stats("org-001")
    assert result == "OK"
    assert captured["incident_filters"] is None

    result2 = service.build_stats("org-001", season="winter", attack_method="malware", region="Moscow")
    assert result2 == "OK"
    assert captured["incident_filters"] is not None
    assert captured["incident_filters"].season == "winter"
    assert captured["attack_method"] == "malware"
    assert service.incident_facets("org-001", db=None) == (["Moscow", "Perm"], ["telecom", "finance"])


def test_auth_service_register_login_and_login_response_branches():
    org = SimpleNamespace(id=1, name="Org", code="org-001")
    repo = FakeAuthRepository(user=None, organization=org, organization_by_code=org)
    service = AuthService(repo)

    payload = UserRegisterRequest(
        first_name="  Ivan ",
        last_name=" Petrov ",
        email="  Ivan@Test.COM ",
        password="Secret12345",
        organization_code=" org-001 ",
    )
    created = service.register(payload)
    assert created.email == "ivan@test.com"
    assert repo.created_user_kwargs["email"] == "ivan@test.com"

    dup_repo = FakeAuthRepository(user=SimpleNamespace(id=1), organization=org, organization_by_code=org)
    with pytest.raises(HTTPException) as dup:
        AuthService(dup_repo).register(payload)
    assert dup.value.status_code == 400

    no_org_repo = FakeAuthRepository(user=None, organization=None, organization_by_code=None)
    with pytest.raises(HTTPException) as missing:
        AuthService(no_org_repo).register(payload)
    assert missing.value.status_code == 404

    hashed_user = SimpleNamespace(
        id=1,
        first_name="Ivan",
        last_name="Petrov",
        email="ivan@test.com",
        hashed_password=repo.created_user_kwargs["hashed_password"],
        organization_id=1,
    )
    login_repo = FakeAuthRepository(user=hashed_user, organization=org, organization_by_code=org)
    login_service = AuthService(login_repo)
    token = login_service.login(LoginRequest(email="ivan@test.com", password="Secret12345"))
    assert decode_token(token.access_token)["sub"] == "ivan@test.com"

    login_response = login_service.build_login_response(LoginRequest(email="ivan@test.com", password="Secret12345"))
    assert login_response.user.organization_name == "Org"

    orgless_repo = FakeAuthRepository(user=hashed_user, organization=None, organization_by_code=org)
    login_response_orgless = AuthService(orgless_repo).build_login_response(
        LoginRequest(email="ivan@test.com", password="Secret12345")
    )
    assert login_response_orgless.user.organization_name == ""


@pytest.mark.asyncio
async def test_invalid_token_format_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth/me", headers={"Authorization": "Bearer definitely-not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["code"] == "http_401"


@pytest.mark.asyncio
async def test_predict_validation_on_negative_vulnerabilities_count():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers, organization_code = await register_and_login_unique(client)
        response = await client.post(
            "/predict",
            headers=headers,
            json={
                "organization_id": organization_code,
                "region": "Moscow",
                "industry": "telecom",
                "season": "winter",
                "day_of_week": 2,
                "hour": 9,
                "asset_type": "vpn_gateway",
                "has_external_access": True,
                "privileged_accounts_count": 12,
                "known_vulnerabilities_count": -1,
            },
        )
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
