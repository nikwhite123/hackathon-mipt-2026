from __future__ import annotations

from app.repositories.config_repository import ConfigRepository
from app.schemas import ThreatFilter, ThreatListResponse


class ThreatCatalogService:
    def __init__(self, repository: ConfigRepository):
        self.repository = repository

    def list_threats(self, threat_filter: ThreatFilter | None = None) -> ThreatListResponse:
        catalog = self.repository.load_threat_catalog()
        items = catalog.threats

        if threat_filter:
            if threat_filter.severity:
                items = [item for item in items if item.severity == threat_filter.severity]
            if threat_filter.category:
                items = [item for item in items if item.category == threat_filter.category]

        return ThreatListResponse(total=len(items), items=items)

    def get_recommendations(self, method: str):
        catalog = self.repository.load_threat_catalog()
        return catalog.recommendations.get(method, [])

    def get_threat_by_id(self, threat_id: str):
        catalog = self.repository.load_threat_catalog()
        for threat in catalog.threats:
            if threat.threat_id == threat_id:
                return threat
        raise KeyError(f"Threat with id '{threat_id}' not found")
