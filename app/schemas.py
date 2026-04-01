from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Season(str, Enum):
    winter = "winter"
    spring = "spring"
    summer = "summer"
    autumn = "autumn"


class TimeOfDay(str, Enum):
    night = "night"
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"


class AttackMethod(str, Enum):
    phishing = "phishing"
    brute_force = "brute_force"
    malware = "malware"
    credential_stuffing = "credential_stuffing"
    ransomware = "ransomware"
    sql_injection = "sql_injection"


class TargetObject(str, Enum):
    crm = "crm"
    web_portal = "web_portal"
    db_server = "db_server"
    file_server = "file_server"
    mail_gateway = "mail_gateway"
    vpn_gateway = "vpn_gateway"
    workstation = "workstation"


class VulnerabilitySeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ThreatSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class PredictRequest(BaseModel):
    organization_id: str = Field(..., examples=["org-001"])
    region: str = Field(..., examples=["Moscow"])
    industry: str = Field(..., examples=["telecom"])
    season: Season
    day_of_week: int = Field(..., ge=1, le=7, description="1=Monday, 7=Sunday")
    hour: int = Field(..., ge=0, le=23)
    asset_type: str = Field(..., examples=["crm"])
    has_external_access: bool = True
    privileged_accounts_count: int = Field(..., ge=0, examples=[12])
    known_vulnerabilities_count: int = Field(..., ge=0, examples=[3])


class ProtectionRecommendation(BaseModel):
    code: str
    title: str
    description: str
    priority: int = Field(..., ge=1, le=5)


class PredictResponse(BaseModel):
    generated_at: datetime
    risk_score: float = Field(..., ge=0, le=1)
    predicted_attack_time_window: str
    predicted_target_object: TargetObject
    predicted_attack_method: AttackMethod
    confidence: float = Field(..., ge=0, le=1)
    recommendations: List[ProtectionRecommendation]
    rationale: List[str]


class ThreatItem(BaseModel):
    threat_id: str
    name: str
    description: str
    category: str
    severity: ThreatSeverity
    likely_targets: List[TargetObject]
    common_methods: List[AttackMethod]
    source: str = "FSTEC mock registry"


class ThreatListResponse(BaseModel):
    total: int
    items: List[ThreatItem]


class ThreatStats(BaseModel):
    total_incidents: int
    top_attack_method: AttackMethod
    top_target_object: TargetObject
    risk_distribution: Dict[str, int]
    incidents_by_season: Dict[str, int]
    incidents_by_time_of_day: Dict[str, int]


class InfrastructureVulnerability(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    vulnerability_code: str
    title: str
    severity: VulnerabilitySeverity
    description: str


class VulnerabilityMapRequest(BaseModel):
    vulnerabilities: List[InfrastructureVulnerability] = Field(..., min_length=1)


class ThreatMatch(BaseModel):
    threat_id: str
    threat_name: str
    severity: ThreatSeverity
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
