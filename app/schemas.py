"""Pydantic models for API request/response bodies and JSON configs (pydantic v1 and v2 field_validator)."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, EmailStr
try:
    from pydantic import field_validator
    PYDANTIC_V2 = True
except ImportError:
    from pydantic import validator as field_validator
    PYDANTIC_V2 = False


def _password_complexity(value: str) -> str:
    if len(value) < 10:
        raise ValueError("Password must be at least 10 characters long.")
    if not any(c.isupper() for c in value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in value):
        raise ValueError("Password must contain at least one digit.")
    return value


def _person_name(value: str, label: str) -> str:
    s = value.strip()
    if len(s) < 2:
        raise ValueError(f"{label}: at least 2 characters after trimming whitespace.")
    if not any(ch.isalpha() for ch in s):
        raise ValueError(f"{label} must contain at least one letter.")
    if len(s) > 100:
        raise ValueError(f"{label}: must be at most 100 characters.")
    return s

Severity = Literal["low", "medium", "high", "critical"]
ThreatMethod = Literal[
    "phishing",
    "brute_force",
    "malware",
    "credential_stuffing",
    "ransomware",
    "sql_injection",
]
TargetType = Literal[
    "crm",
    "web_portal",
    "db_server",
    "file_server",
    "mail_gateway",
    "vpn_gateway",
    "workstation",
]
SeasonType = Literal["winter", "spring", "summer", "autumn"]
TimeOfDay = Literal["night", "morning", "afternoon", "evening"]


class ProtectionRecommendation(BaseModel):
    code: str
    title: str
    description: str
    priority: int = Field(..., ge=1, le=5)


class ThreatReference(BaseModel):
    threat_id: str
    name: str
    description: str
    category: str
    severity: Severity
    likely_targets: List[TargetType]
    common_methods: List[ThreatMethod]
    source: str = "FSTEC threat catalog"




class OrganizationResponse(BaseModel):
    id: int
    name: str
    code: str | None = None

    if PYDANTIC_V2:
        model_config = {"from_attributes": True}
    else:
        class Config:
            orm_mode = True


class UserRegisterRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=10, max_length=128)
    organization_code: str = Field(..., min_length=1, max_length=64)

    if PYDANTIC_V2:
        @field_validator("first_name", "last_name", mode="before")
        @classmethod
        def _strip_person_fields(cls, value):
            return value.strip() if isinstance(value, str) else value

        @field_validator("first_name")
        @classmethod
        def _validate_first_name(cls, value: str) -> str:
            return _person_name(value, "First name")

        @field_validator("last_name")
        @classmethod
        def _validate_last_name(cls, value: str) -> str:
            return _person_name(value, "Last name")

        @field_validator("email", mode="before")
        @classmethod
        def _normalize_email_register(cls, value):
            return value.strip().lower() if isinstance(value, str) else value

        @field_validator("password")
        @classmethod
        def _validate_password_register(cls, value: str) -> str:
            return _password_complexity(value)

        @field_validator("organization_code", mode="before")
        @classmethod
        def _strip_org_code(cls, value):
            return value.strip() if isinstance(value, str) else value
    else:
        @field_validator("first_name", "last_name", pre=True)
        def _strip_person_fields(cls, value):  # type: ignore[misc]
            return value.strip() if isinstance(value, str) else value

        @field_validator("first_name")
        def _validate_first_name(cls, value: str) -> str:  # type: ignore[misc]
            return _person_name(value, "First name")

        @field_validator("last_name")
        def _validate_last_name(cls, value: str) -> str:  # type: ignore[misc]
            return _person_name(value, "Last name")

        @field_validator("email", pre=True)
        def _normalize_email_register(cls, value):  # type: ignore[misc]
            return value.strip().lower() if isinstance(value, str) else value

        @field_validator("password")
        def _validate_password_register(cls, value: str) -> str:  # type: ignore[misc]
            return _password_complexity(value)

        @field_validator("organization_code", pre=True)
        def _strip_org_code(cls, value):  # type: ignore[misc]
            return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    if PYDANTIC_V2:
        @field_validator("email", mode="before")
        @classmethod
        def _normalize_email_login(cls, value):
            return value.strip().lower() if isinstance(value, str) else value
    else:
        @field_validator("email", pre=True)
        def _normalize_email_login(cls, value):  # type: ignore[misc]
            return value.strip().lower() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    organization_id: int
    organization_name: str
    organization_code: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserLoginResponse(TokenResponse):
    user: UserResponse


class OrganizationSettingsRequest(BaseModel):
    region: str = Field(..., min_length=1, max_length=64)
    industry: str = Field(..., min_length=1, max_length=64)
    host_count: int = Field(..., ge=1)
    technologies: List[str] = Field(default_factory=list)


class OrganizationSettingsResponse(OrganizationSettingsRequest):
    organization_id: int

class PredictRequest(BaseModel):
    organization_id: str = Field(
        ...,
        examples=["org-001"],
        description="Organization code from the directory. The legacy field name is kept for backward compatibility.",
    )
    region: str = Field(..., examples=["Moscow"])
    industry: str = Field(..., examples=["telecom"])
    season: SeasonType
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    hour: int = Field(..., ge=0, le=23)
    asset_type: TargetType
    has_external_access: bool = True
    privileged_accounts_count: int = Field(..., ge=0, examples=[12])
    known_vulnerabilities_count: int = Field(..., ge=0, examples=[3])
    prefer_ml: bool = Field(
        default=False,
        description="If true, use the ML model for predicted target and attack method. "
        "Risk score and attack time window remain heuristic.",
    )


class PredictTimeResponse(BaseModel):
    generated_at: datetime
    predicted_attack_time_window: str
    confidence: float = Field(..., ge=0, le=1)
    rationale: List[str]


class PredictTargetResponse(BaseModel):
    generated_at: datetime
    predicted_target_object: TargetType
    confidence: float = Field(..., ge=0, le=1)
    rationale: List[str]


class PredictMethodResponse(BaseModel):
    generated_at: datetime
    predicted_attack_method: ThreatMethod
    confidence: float = Field(..., ge=0, le=1)
    rationale: List[str]


class PredictRecommendationsResponse(BaseModel):
    generated_at: datetime
    predicted_attack_method: ThreatMethod
    predicted_target_object: TargetType
    recommendations: List[ProtectionRecommendation]
    confidence: float = Field(..., ge=0, le=1)


class PredictResponse(BaseModel):
    generated_at: datetime
    risk_score: float = Field(..., ge=0, le=1)
    predicted_attack_time_window: str
    predicted_target_object: TargetType
    predicted_attack_method: ThreatMethod
    confidence: float = Field(..., ge=0, le=1)
    recommendations: List[ProtectionRecommendation]
    rationale: List[str]


class ThreatListResponse(BaseModel):
    total: int
    items: List[ThreatReference]


class ThreatStats(BaseModel):
    total_incidents: int
    top_attack_method: ThreatMethod
    top_target_object: TargetType
    risk_distribution: Dict[str, int]
    incidents_by_season: Dict[str, int]
    incidents_by_time_of_day: Dict[str, int]
    incidents_by_hour: Dict[int, int]
    incidents_by_region: Dict[str, int]
    incidents_by_target_object: Dict[str, int]
    incidents_by_month: Dict[str, int] = Field(
        default_factory=dict,
        description="Keys are YYYY-MM strings; values are incident counts",
    )
    incidents_by_attack_method: Dict[str, int] = Field(default_factory=dict)


class StatsFacetsResponse(BaseModel):
    """Distinct region and industry values in incidents for the current organization (UI filter options)."""

    regions: List[str]
    industries: List[str]


class InfrastructureVulnerability(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: TargetType
    vulnerability_code: str
    title: str
    severity: Severity
    description: str


class VulnerabilityMapRequest(BaseModel):
    vulnerabilities: List[InfrastructureVulnerability]

    if PYDANTIC_V2:
        @field_validator("vulnerabilities")
        @classmethod
        def validate_vulnerabilities_not_empty(cls, value: List[InfrastructureVulnerability]) -> List[InfrastructureVulnerability]:
            if not value:
                raise ValueError("At least one vulnerability is required")
            return value
    else:
        @field_validator("vulnerabilities")
        def validate_vulnerabilities_not_empty(cls, value: List[InfrastructureVulnerability]) -> List[InfrastructureVulnerability]:
            if not value:
                raise ValueError("At least one vulnerability is required")
            return value


class ThreatMatch(BaseModel):
    threat: ThreatReference
    match_score: float = Field(..., ge=0, le=1)
    reason: str
    recommended_actions: List[ProtectionRecommendation]


class VulnerabilityMappingItem(BaseModel):
    asset_id: str
    asset_name: str
    vulnerability_code: str
    matches: List[ThreatMatch]


class VulnerabilityMapResponse(BaseModel):
    total_assets: int
    total_vulnerabilities: int
    items: List[VulnerabilityMappingItem]


class ErrorResponse(BaseModel):
    """Unified API error shape (4xx/5xx and validation errors)."""

    detail: str
    errors: List[dict] | None = None
    request_id: str | None = None
    code: str | None = None


class ThreatFilter(BaseModel):
    severity: Severity | None = None
    category: str | None = None


class RuleConfig(BaseModel):
    tokens: List[str]
    threat_id: str
    match_score: float = Field(..., ge=0, le=1)
    reason: str
    recommendation_method: ThreatMethod


    if PYDANTIC_V2:
        @field_validator("tokens")
        @classmethod
        def validate_tokens_not_empty(cls, value: List[str]) -> List[str]:
            if not value:
                raise ValueError("tokens must not be empty")
            return value
    else:
        @field_validator("tokens")
        def validate_tokens_not_empty(cls, value: List[str]) -> List[str]:
            if not value:
                raise ValueError("tokens must not be empty")
            return value


class ScoringConfig(BaseModel):
    vulnerability_count_weight: float = Field(..., gt=0)
    attack_intensity_weight: float = Field(..., gt=0)
    asset_criticality_weight: float = Field(..., gt=0)
    risk_score_normalizer: float = Field(..., gt=0)
    confidence_base: float = Field(..., ge=0, le=1)
    confidence_multiplier: float = Field(..., ge=0, le=1)
    asset_criticality_by_target: Dict[TargetType, float]

    if PYDANTIC_V2:
        @field_validator('asset_criticality_by_target')
        @classmethod
        def validate_asset_criticality(cls, value: Dict[TargetType, float]) -> Dict[TargetType, float]:
            if any(score < 0 for score in value.values()):
                raise ValueError('asset criticality values must be non-negative')
            return value
    else:
        @field_validator('asset_criticality_by_target')
        def validate_asset_criticality(cls, value: Dict[TargetType, float]) -> Dict[TargetType, float]:
            if any(score < 0 for score in value.values()):
                raise ValueError('asset criticality values must be non-negative')
            return value


class ThreatCatalogConfig(BaseModel):
    threats: List[ThreatReference]
    recommendations: Dict[str, List[ProtectionRecommendation]]

    if PYDANTIC_V2:
        @field_validator("threats")
        @classmethod
        def validate_threats_not_empty(cls, value: List[ThreatReference]) -> List[ThreatReference]:
            if not value:
                raise ValueError("threats must not be empty")
            return value
    else:
        @field_validator("threats")
        def validate_threats_not_empty(cls, value: List[ThreatReference]) -> List[ThreatReference]:
            if not value:
                raise ValueError("threats must not be empty")
            return value

    if PYDANTIC_V2:
        @field_validator("recommendations")
        @classmethod
        def validate_recommendation_keys(
            cls, value: Dict[str, List[ProtectionRecommendation]]
        ) -> Dict[str, List[ProtectionRecommendation]]:
            allowed = {
                "phishing",
                "brute_force",
                "malware",
                "credential_stuffing",
                "ransomware",
                "sql_injection",
            }
            invalid = sorted(set(value) - allowed)
            if invalid:
                raise ValueError(f"Unsupported recommendation keys: {invalid}")
            return value
    else:
        @field_validator("recommendations")
        def validate_recommendation_keys(
            cls, value: Dict[str, List[ProtectionRecommendation]]
        ) -> Dict[str, List[ProtectionRecommendation]]:
            allowed = {
                "phishing",
                "brute_force",
                "malware",
                "credential_stuffing",
                "ransomware",
                "sql_injection",
            }
            invalid = sorted(set(value) - allowed)
            if invalid:
                raise ValueError(f"Unsupported recommendation keys: {invalid}")
            return value