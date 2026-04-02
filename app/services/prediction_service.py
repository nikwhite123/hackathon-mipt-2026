from __future__ import annotations

from datetime import datetime, UTC

from app.processors.scoring import ThreatScoringProcessor
from app.schemas import PredictRequest, PredictResponse
from app.services.threat_catalog_service import ThreatCatalogService


class PredictionService:
    def __init__(self, scoring_processor: ThreatScoringProcessor, threat_catalog_service: ThreatCatalogService):
        self.scoring_processor = scoring_processor
        self.threat_catalog_service = threat_catalog_service

    def predict(self, payload: PredictRequest) -> PredictResponse:
        scoring = self.scoring_processor.score(payload)
        target = payload.asset_type
        method = self._detect_attack_method(target)
        recommendations = self.threat_catalog_service.get_recommendations(method)

        return PredictResponse(
            generated_at=datetime.now(UTC),
            risk_score=scoring.risk_score,
            predicted_attack_time_window=self._detect_time_bucket(payload.hour),
            predicted_target_object=target,
            predicted_attack_method=method,
            confidence=scoring.confidence,
            recommendations=recommendations,
            rationale=scoring.rationale,
        )

    @staticmethod
    def _detect_time_bucket(hour: int) -> str:
        if 0 <= hour <= 5:
            return "00:00-06:00"
        if 6 <= hour <= 11:
            return "06:00-12:00"
        if 12 <= hour <= 17:
            return "12:00-18:00"
        return "18:00-24:00"

    @staticmethod
    def _detect_attack_method(target: str) -> str:
        method_mapping = {
            "crm": "phishing",
            "mail_gateway": "phishing",
            "vpn_gateway": "brute_force",
            "web_portal": "sql_injection",
            "db_server": "sql_injection",
            "file_server": "ransomware",
            "workstation": "malware",
        }
        return method_mapping.get(target, "malware")
