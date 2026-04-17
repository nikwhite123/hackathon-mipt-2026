from __future__ import annotations

from app.repositories.data_repository import DataRepository


class RiskContextService:
    def __init__(self, repository: DataRepository):
        self.repository = repository

    def get_attack_intensity(self, region: str, hour: int, season: str, organization_code: str | None = None) -> float:
        incidents = self.repository.load_incidents_by_organization_code(organization_code)
        if incidents.empty:
            incidents = self.repository.load_incidents()
        scope = incidents[
            (incidents['region'].astype(str).str.casefold() == region.casefold())
            & (incidents['season'] == season)
        ]
        if scope.empty:
            scope = incidents[incidents['season'] == season]
        if scope.empty:
            scope = incidents

        hourly = scope.groupby('hour').size()
        current = int(hourly.get(hour, 0))
        baseline = max(float(hourly.mean()), 1.0)
        return round(current / baseline, 2)
