from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field, field_validator

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
    source: str = "FSTEC mock registry"


class PredictRequest(BaseModel):
    organization_id: str = Field(..., examples=["org-001"])
    region: str = Field(..., examples=["Moscow"])
    industry: str = Field(..., examples=["telecom"])
    season: SeasonType
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    hour: int = Field(..., ge=0, le=23)
    asset_type: TargetType
    has_external_access: bool = True
    privileged_accounts_count: int = Field(..., ge=0, examples=[12])
    known_vulnerabilities_count: int = Field(..., ge=0, examples=[3])


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


class InfrastructureVulnerability(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: TargetType
    vulnerability_code: str
    title: str
    severity: Severity
    description: str


class VulnerabilityMapRequest(BaseModel):
    vulnerabilities: List[InfrastructureVulnerability] = Field(..., min_length=1)


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
    detail: str
    errors: List[dict] | None = None


class ThreatFilter(BaseModel):
    severity: Severity | None = None
    category: str | None = None


class RuleConfig(BaseModel):
    tokens: List[str] = Field(..., min_length=1)
    threat_id: str
    match_score: float = Field(..., ge=0, le=1)
    reason: str
    recommendation_method: ThreatMethod


class ScoringConfig(BaseModel):
    base_risk: float = Field(..., ge=0, le=1)
    external_access_weight: float = Field(..., ge=0, le=1)
    known_vulnerabilities_weight: float = Field(..., ge=0, le=1)
    privileged_accounts_weight: float = Field(..., ge=0, le=1)
    peak_hours_weight: float = Field(..., ge=0, le=1)
    peak_hours: List[int]
    confidence_base: float = Field(..., ge=0, le=1)
    confidence_multiplier: float = Field(..., ge=0, le=1)

    @field_validator("peak_hours")
    @classmethod
    def validate_peak_hours(cls, value: List[int]) -> List[int]:
        if any(hour < 0 or hour > 23 for hour in value):
            raise ValueError("peak_hours must contain values from 0 to 23")
        return value


class ThreatCatalogConfig(BaseModel):
    threats: List[ThreatReference] = Field(..., min_length=1)
    recommendations: Dict[str, List[ProtectionRecommendation]]

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