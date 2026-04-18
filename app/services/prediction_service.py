"""Assemble prediction responses: scoring, optional ML branch, catalog recommendations."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.processors.scoring import ThreatScoringProcessor
from app.schemas import (
    PredictMethodResponse,
    PredictRecommendationsResponse,
    PredictRequest,
    PredictResponse,
    PredictTargetResponse,
    PredictTimeResponse,
)
from app.services.ml_prediction_model_service import MlPredictionModelService
from app.services.threat_catalog_service import ThreatCatalogService


class PredictionService:
    """Facade over scoring, ML inference, and the recommendation catalog."""

    def __init__(
        self,
        scoring_processor: ThreatScoringProcessor,
        threat_catalog_service: ThreatCatalogService,
        ml_model_service: MlPredictionModelService,
    ):
        self.scoring_processor = scoring_processor
        self.threat_catalog_service = threat_catalog_service
        self.ml_model_service = ml_model_service

    def predict(self, payload: PredictRequest, db: Session | None = None) -> PredictResponse:
        """Build scoring + ML context and return the full prediction DTO."""
        prediction_context = self._build_prediction_context(payload, db=db)
        return PredictResponse(**prediction_context)

    def predict_time(self, payload: PredictRequest, db: Session | None = None) -> PredictTimeResponse:
        """Return only the time-window slice of the prediction context."""
        prediction_context = self._build_prediction_context(payload, db=db)
        return PredictTimeResponse(
            generated_at=prediction_context["generated_at"],
            predicted_attack_time_window=prediction_context["predicted_attack_time_window"],
            confidence=prediction_context["confidence"],
            rationale=prediction_context["rationale"],
        )

    def predict_target(self, payload: PredictRequest, db: Session | None = None) -> PredictTargetResponse:
        """Return only the predicted target asset type slice."""
        prediction_context = self._build_prediction_context(payload, db=db)
        return PredictTargetResponse(
            generated_at=prediction_context["generated_at"],
            predicted_target_object=prediction_context["predicted_target_object"],
            confidence=prediction_context["confidence"],
            rationale=prediction_context["rationale"],
        )

    def predict_method(self, payload: PredictRequest, db: Session | None = None) -> PredictMethodResponse:
        """Return only the predicted attack method slice."""
        prediction_context = self._build_prediction_context(payload, db=db)
        return PredictMethodResponse(
            generated_at=prediction_context["generated_at"],
            predicted_attack_method=prediction_context["predicted_attack_method"],
            confidence=prediction_context["confidence"],
            rationale=prediction_context["rationale"],
        )

    def get_recommendations(self, payload: PredictRequest, db: Session | None = None) -> PredictRecommendationsResponse:
        """Return recommendations and confidence without redundant risk fields."""
        prediction_context = self._build_prediction_context(payload, db=db)
        return PredictRecommendationsResponse(
            generated_at=prediction_context["generated_at"],
            predicted_attack_method=prediction_context["predicted_attack_method"],
            predicted_target_object=prediction_context["predicted_target_object"],
            recommendations=prediction_context["recommendations"],
            confidence=prediction_context["confidence"],
        )

    def _build_prediction_context(self, payload: PredictRequest, db: Session | None = None) -> dict:
        """Shared context dict for all /predict* response shapes."""
        scoring = self.scoring_processor.score(payload, db=db)
        target = payload.asset_type
        method = self._detect_attack_method(target)
        recommendations = self.threat_catalog_service.get_recommendations(method)
        confidence = scoring.confidence
        rationale = list(scoring.rationale)

        if payload.prefer_ml:
            ml_result = self.ml_model_service.predict(payload, db=db)
            if ml_result:
                target = ml_result.target_object
                method = ml_result.attack_method
                confidence = ml_result.confidence
                rationale.append(
                    "ML mode is active: target object and attack method come from the model; "
                    "risk score and attack time window remain heuristic.",
                )
                rationale.extend(ml_result.rationale)
            else:
                rationale.append(
                    "ML prediction was requested, but model output was unavailable. Heuristic target and method were used.",
                )

        recommendations = self.threat_catalog_service.get_recommendations(method)

        return {
            "generated_at": datetime.now(UTC),
            "risk_score": scoring.risk_score,
            "predicted_attack_time_window": self._detect_time_bucket(payload.hour),
            "predicted_target_object": target,
            "predicted_attack_method": method,
            "confidence": confidence,
            "recommendations": recommendations,
            "rationale": rationale,
        }

    @staticmethod
    def _detect_time_bucket(hour: int) -> str:
        """Map hour-of-day to a coarse label used in API responses."""
        if 0 <= hour <= 5:
            return "00:00-06:00"
        if 6 <= hour <= 11:
            return "06:00-12:00"
        if 12 <= hour <= 17:
            return "12:00-18:00"
        return "18:00-24:00"

    @staticmethod
    def _detect_attack_method(target: str) -> str:
        """Heuristic default attack method when ML confidence is below the threshold."""
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
