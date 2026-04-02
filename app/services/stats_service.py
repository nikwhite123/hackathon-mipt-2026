from __future__ import annotations

from app.schemas import ThreatStats


class StatsService:
    def build_stats(self) -> ThreatStats:
        return ThreatStats(
            total_incidents=2000,
            top_attack_method="phishing",
            top_target_object="crm",
            risk_distribution={"low": 180, "medium": 950, "high": 620, "critical": 250},
            incidents_by_season={"winter": 430, "spring": 510, "summer": 470, "autumn": 590},
            incidents_by_time_of_day={"night": 280, "morning": 620, "afternoon": 540, "evening": 560},
        )
