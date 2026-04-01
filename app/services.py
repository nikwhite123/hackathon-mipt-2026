from __future__ import annotations

from datetime import datetime
from typing import List

from app.data import RECOMMENDATIONS, THREATS
from app.schemas import (
    AttackMethod,
    PredictRequest,
    PredictResponse,
    ProtectionRecommendation,
    TargetObject,
    ThreatItem,
    ThreatListResponse,
    ThreatMatch,
    ThreatStats,
    VulnerabilityMapRequest,
    VulnerabilityMapResponse,
    VulnerabilityMappingItem,
)


def _detect_time_bucket(hour: int) -> str:
    if 0 <= hour <= 5:
        return "00:00-06:00"
    if 6 <= hour <= 11:
        return "06:00-12:00"
    if 12 <= hour <= 17:
        return "12:00-18:00"
    return "18:00-24:00"


def generate_prediction(payload: PredictRequest) -> PredictResponse:
    risk = 0.25
    rationale: List[str] = []

    if payload.has_external_access:
        risk += 0.15
        rationale.append("У актива есть внешний доступ, риск первичного проникновения выше.")

    if payload.known_vulnerabilities_count >= 3:
        risk += 0.2
        rationale.append("Обнаружено несколько известных уязвимостей.")

    if payload.privileged_accounts_count >= 10:
        risk += 0.1
        rationale.append("Большое число привилегированных учетных записей повышает риск компрометации.")

    if payload.hour in (8, 9, 10, 18, 19, 20):
        risk += 0.1
        rationale.append("Временное окно совпадает с повышенной активностью атакующих.")

    asset_mapping = {
        "crm": TargetObject.crm,
        "web": TargetObject.web_portal,
        "db": TargetObject.db_server,
        "mail": TargetObject.mail_gateway,
        "vpn": TargetObject.vpn_gateway,
        "file": TargetObject.file_server,
        "workstation": TargetObject.workstation,
    }
    target = asset_mapping.get(payload.asset_type.lower(), TargetObject.workstation)

    if target in (TargetObject.crm, TargetObject.mail_gateway):
        method = AttackMethod.phishing
    elif target == TargetObject.vpn_gateway:
        method = AttackMethod.brute_force
    elif target in (TargetObject.web_portal, TargetObject.db_server):
        method = AttackMethod.sql_injection
    elif target == TargetObject.file_server:
        method = AttackMethod.ransomware
    else:
        method = AttackMethod.malware

    risk = min(round(risk, 2), 0.99)
    confidence = min(round(0.55 + risk / 2, 2), 0.98)
    recs = [ProtectionRecommendation(**item) for item in RECOMMENDATIONS.get(method, [])]

    return PredictResponse(
        generated_at=datetime.utcnow(),
        risk_score=risk,
        predicted_attack_time_window=_detect_time_bucket(payload.hour),
        predicted_target_object=target,
        predicted_attack_method=method,
        confidence=confidence,
        recommendations=recs,
        rationale=rationale or ["Прогноз сформирован по базовым эвристикам mock-модели."],
    )


def list_threats() -> ThreatListResponse:
    items = [ThreatItem(**item) for item in THREATS]
    return ThreatListResponse(total=len(items), items=items)


def build_stats() -> ThreatStats:
    return ThreatStats(
        total_incidents=2000,
        top_attack_method=AttackMethod.phishing,
        top_target_object=TargetObject.crm,
        risk_distribution={"low": 180, "medium": 950, "high": 620, "critical": 250},
        incidents_by_season={"winter": 430, "spring": 510, "summer": 470, "autumn": 590},
        incidents_by_time_of_day={"night": 280, "morning": 620, "afternoon": 540, "evening": 560},
    )


def map_vulnerabilities(payload: VulnerabilityMapRequest) -> VulnerabilityMapResponse:
    items: List[VulnerabilityMappingItem] = []

    for vuln in payload.vulnerabilities:
        matches: List[ThreatMatch] = []
        title = vuln.title.lower()
        desc = vuln.description.lower()
        code = vuln.vulnerability_code.lower()

        if any(token in f"{title} {desc} {code}" for token in ["password", "auth", "vpn", "login"]):
            matches.append(
                ThreatMatch(
                    threat_id="TH-003",
                    threat_name="Атака на VPN-шлюз через подбор пароля",
                    severity="high",
                    match_score=0.91,
                    reason="Совпадение по признакам слабой аутентификации или удаленного доступа.",
                    recommended_actions=[
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.brute_force][0]),
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.brute_force][1]),
                    ],
                )
            )

        if any(token in f"{title} {desc} {code}" for token in ["sql", "input", "query", "web"]):
            matches.append(
                ThreatMatch(
                    threat_id="TH-004",
                    threat_name="SQL-инъекция в веб-портал",
                    severity="medium",
                    match_score=0.88,
                    reason="Описание уязвимости похоже на проблемы валидации ввода или БД-запросов.",
                    recommended_actions=[
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.sql_injection][0]),
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.sql_injection][1]),
                    ],
                )
            )

        if any(token in f"{title} {desc} {code}" for token in ["mail", "phish", "attachment", "macro"]):
            matches.append(
                ThreatMatch(
                    threat_id="TH-001",
                    threat_name="Компрометация CRM через фишинговую рассылку",
                    severity="high",
                    match_score=0.84,
                    reason="Есть связь с почтой, вложениями или фишинговым вектором доставки.",
                    recommended_actions=[
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.phishing][0]),
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.phishing][1]),
                    ],
                )
            )

        if not matches:
            matches.append(
                ThreatMatch(
                    threat_id="TH-005",
                    threat_name="Вредоносное ПО на рабочей станции",
                    severity="medium",
                    match_score=0.62,
                    reason="Использован fallback-matching по общему классу endpoint-рисков.",
                    recommended_actions=[
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.malware][0]),
                        ProtectionRecommendation(**RECOMMENDATIONS[AttackMethod.malware][1]),
                    ],
                )
            )

        items.append(
            VulnerabilityMappingItem(
                asset_id=vuln.asset_id,
                asset_name=vuln.asset_name,
                vulnerability_code=vuln.vulnerability_code,
                matches=matches,
            )
        )

    return VulnerabilityMapResponse(
        total_assets=len({item.asset_id for item in payload.vulnerabilities}),
        total_vulnerabilities=len(payload.vulnerabilities),
        items=items,
    )
