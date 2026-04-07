from __future__ import annotations

from functools import lru_cache

from app.processors.scoring import ThreatScoringProcessor
from app.repositories.config_repository import get_config_repository
from app.schemas import RuleConfig
from app.services.prediction_service import PredictionService
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService
from app.strategies.vulnerability_mapping import RuleBasedThreatMatchingStrategy


@lru_cache(maxsize=1)
def get_threat_catalog_service() -> ThreatCatalogService:
    return ThreatCatalogService(get_config_repository())


@lru_cache(maxsize=1)
def get_prediction_service() -> PredictionService:
    repository = get_config_repository()
    scoring_processor = ThreatScoringProcessor(repository.load_scoring_config())
    return PredictionService(scoring_processor, get_threat_catalog_service())


@lru_cache(maxsize=1)
def get_stats_service() -> StatsService:
    return StatsService()


@lru_cache(maxsize=1)
def get_vulnerability_mapping_service() -> VulnerabilityMappingService:
    repository = get_config_repository()
    threat_catalog_service = get_threat_catalog_service()
    rules: list[RuleConfig] = repository.load_mapping_rules()

    strategies = [
        RuleBasedThreatMatchingStrategy(rule, threat_catalog_service)
        for rule in rules
        if rule.threat_id != "TH-005"
    ]
    fallback_rule = next(rule for rule in rules if rule.threat_id == "TH-005")
    fallback_strategy = RuleBasedThreatMatchingStrategy(fallback_rule, threat_catalog_service)
    return VulnerabilityMappingService(strategies, fallback_strategy)
