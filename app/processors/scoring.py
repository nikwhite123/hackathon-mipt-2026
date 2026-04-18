"""Compute risk_score and confidence from scoring.json and attack context."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.schemas import PredictRequest, ScoringConfig
from app.services.risk_context_service import RiskContextService


@dataclass
class ScoringResult:
    """Scoring output for a prediction response and rationale."""

    risk_score: float
    confidence: float
    rationale: list[str] = field(default_factory=list)
    attack_intensity: float = 0.0
    asset_criticality: float = 0.0


class ThreatScoringProcessor:
    """Weighted blend of vulnerability count, attack intensity, and asset criticality."""

    def __init__(self, config: ScoringConfig, risk_context_service: RiskContextService):
        self.config = config
        self.risk_context_service = risk_context_service

    def score(self, payload: PredictRequest, db: Session | None = None) -> ScoringResult:
        """Return ScoringResult with capped risk_score and confidence."""
        attack_intensity = self.risk_context_service.get_attack_intensity(
            region=payload.region,
            hour=payload.hour,
            season=payload.season,
            organization_code=payload.organization_id,
            industry=payload.industry,
            db=db,
        )
        asset_criticality = self.config.asset_criticality_by_target[payload.asset_type]

        raw_score = (
            self.config.vulnerability_count_weight * payload.known_vulnerabilities_count
            + self.config.attack_intensity_weight * attack_intensity
            + self.config.asset_criticality_weight * asset_criticality
        )
        risk = min(round(raw_score / self.config.risk_score_normalizer, 2), 0.99)
        confidence = min(round(self.config.confidence_base + risk * self.config.confidence_multiplier, 2), 0.98)

        rationale = [
            f'Known vulnerability count considered: {payload.known_vulnerabilities_count}.',
            (
                f'Attack intensity from history (region, season, hour; with enough data — '
                f'industry {payload.industry}): {attack_intensity:.2f}.'
            ),
            f'Asset criticality for {payload.asset_type}: {asset_criticality:.2f}.',
        ]
        if payload.has_external_access:
            rationale.append('The asset has external exposure, which raises response priority.')
        if payload.privileged_accounts_count >= 10:
            rationale.append('A large number of privileged accounts increases the attack surface.')

        return ScoringResult(
            risk_score=risk,
            confidence=confidence,
            rationale=rationale,
            attack_intensity=attack_intensity,
            asset_criticality=asset_criticality,
        )
