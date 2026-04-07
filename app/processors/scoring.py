from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import PredictRequest, ScoringConfig


@dataclass
class ScoringResult:
    risk_score: float
    confidence: float
    rationale: list[str] = field(default_factory=list)


class ThreatScoringProcessor:
    def __init__(self, config: ScoringConfig):
        self.config = config

    def score(self, payload: PredictRequest) -> ScoringResult:
        risk = self.config.base_risk
        rationale: list[str] = []

        if payload.has_external_access:
            risk += self.config.external_access_weight
            rationale.append("У актива есть внешний доступ, риск первичного проникновения выше.")

        if payload.known_vulnerabilities_count >= 3:
            risk += self.config.known_vulnerabilities_weight
            rationale.append("Обнаружено несколько известных уязвимостей.")

        if payload.privileged_accounts_count >= 10:
            risk += self.config.privileged_accounts_weight
            rationale.append("Большое число привилегированных учетных записей повышает риск компрометации.")

        if payload.hour in self.config.peak_hours:
            risk += self.config.peak_hours_weight
            rationale.append("Временное окно совпадает с повышенной активностью атакующих.")

        risk = min(round(risk, 2), 0.99)
        confidence = min(round(self.config.confidence_base + risk * self.config.confidence_multiplier, 2), 0.98)

        if not rationale:
            rationale.append("Прогноз сформирован по базовым эвристикам mock-модели.")

        return ScoringResult(risk_score=risk, confidence=confidence, rationale=rationale)
