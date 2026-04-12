from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import PredictRequest, ScoringConfig


@dataclass
class ScoringResult:
    risk_score: float
    confidence: float
    rationale: list[str] = field(default_factory=list)
    attack_intensity: float = 0.0
    asset_criticality: float = 0.0


class ThreatScoringProcessor:
    def __init__(self, config: ScoringConfig, analytics_service):
        self.config = config
        self.analytics_service = analytics_service

    def score(self, payload: PredictRequest) -> ScoringResult:
        attack_intensity = self.analytics_service.get_attack_intensity(
            region=payload.region,
            hour=payload.hour,
            season=payload.season,
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
            f'Учитывается число известных уязвимостей: {payload.known_vulnerabilities_count}.',
            f'Интенсивность атак по историческим данным для региона/часа/сезона: {attack_intensity:.2f}.',
            f'Критичность актива {payload.asset_type}: {asset_criticality:.2f}.',
        ]
        if payload.has_external_access:
            rationale.append('У актива есть внешний доступ, это усиливает приоритет реагирования.')
        if payload.privileged_accounts_count >= 10:
            rationale.append('Большое число привилегированных учётных записей увеличивает поверхность атаки.')

        return ScoringResult(
            risk_score=risk,
            confidence=confidence,
            rationale=rationale,
            attack_intensity=attack_intensity,
            asset_criticality=asset_criticality,
        )
