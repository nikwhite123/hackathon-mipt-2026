from __future__ import annotations

from app.repositories.data_repository import DataRepository
from app.schemas import ThreatStats
from app.services.analytics_service import AnalyticsService


class StatsService:
    def __init__(self, repository: DataRepository):
        self.analytics_service = AnalyticsService(repository)

    def build_stats(self) -> ThreatStats:
        return self.analytics_service.build_stats()
