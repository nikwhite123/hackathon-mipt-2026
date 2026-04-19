"""Normalized attack intensity by hour, season, and region relative to incident history."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.data_repository import DataRepository


class RiskContextService:
    """Derives incident aggregates used by ThreatScoringProcessor."""

    def __init__(self, repository: DataRepository):
        self.repository = repository

    def get_attack_intensity(
        self,
        region: str,
        hour: int,
        season: str,
        organization_code: str | None = None,
        industry: str | None = None,
        db: Session | None = None,
    ) -> float:
        """Ratio of incidents in the current hour to the hourly mean for the chosen scope (region/season/industry)."""
        incidents = self.repository.load_incidents_by_organization_code(organization_code, db=db)
        if incidents.empty:
            incidents = self.repository.load_incidents(db=db)
        scope = incidents[
            (incidents['region'].astype(str).str.casefold() == region.casefold())
            & (incidents['season'] == season)
        ]
        if scope.empty:
            scope = incidents[incidents['season'] == season]
        if scope.empty:
            scope = incidents

        if industry and not scope.empty and 'industry' in scope.columns:
            ind = str(industry).strip().casefold()
            narrowed = scope[scope['industry'].astype(str).str.casefold() == ind]
            if len(narrowed) >= 3:
                scope = narrowed

        hourly = scope.groupby('hour').size()
        current = int(hourly.to_dict().get(hour, 0))
        mean_value = float(hourly.mean()) if not hourly.empty else 0.0
        baseline = max(mean_value, 1.0) if mean_value == mean_value else 1.0
        return round(current / baseline, 2)
