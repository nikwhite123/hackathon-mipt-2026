"""Thin wrapper over AnalyticsService for GET /stats."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.repositories.data_repository import DataRepository, IncidentQueryFilters
from app.schemas import SeasonType, ThreatMethod, ThreatStats, TimeOfDay
from app.services.analytics_service import AnalyticsService


class StatsService:
    """Aggregated incident statistics for the caller's organization."""

    def __init__(self, repository: DataRepository):
        self.analytics_service = AnalyticsService(repository)

    def build_stats(
        self,
        organization_code: str | None = None,
        *,
        season: SeasonType | None = None,
        attack_method: ThreatMethod | None = None,
        region: str | None = None,
        industry: str | None = None,
        success: int | None = None,
        time_of_day: TimeOfDay | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        threat_code: int | None = None,
        db: Session | None = None,
    ) -> ThreatStats:
        """Build ThreatStats; incident column filters run in SQL when a DB session is provided."""
        incident_filters = IncidentQueryFilters(
            season=season,
            region=region,
            industry=industry,
            success=success,
            time_of_day=time_of_day,
            date_from=date_from,
            date_to=date_to,
            threat_code=threat_code,
        )
        sql_filters = incident_filters if incident_filters.has_any() else None
        return self.analytics_service.build_stats(
            organization_code,
            incident_filters=sql_filters,
            attack_method=attack_method,
            db=db,
        )

    def incident_facets(self, organization_code: str, db: Session) -> tuple[list[str], list[str]]:
        """Distinct region and industry values in the DB for the organization."""
        return self.analytics_service.repository.distinct_incident_facets(organization_code, db)
