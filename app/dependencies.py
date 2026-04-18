"""Cached service factories for FastAPI Depends (one instance per process)."""

from __future__ import annotations

from functools import lru_cache

from app.processors.scoring import ThreatScoringProcessor
from app.repositories.config_repository import get_config_repository
from app.repositories.data_repository import get_data_repository
from app.schemas import RuleConfig
from app.services.ml_prediction_model_service import MlPredictionModelService
from app.services.organization_settings_service import OrganizationSettingsService
from app.services.prediction_service import PredictionService
from app.services.risk_context_service import RiskContextService
from app.services.stats_service import StatsService
from app.services.threat_catalog_service import ThreatCatalogService
from app.services.vulnerability_mapping_service import VulnerabilityMappingService
from app.strategies.vulnerability_mapping import RuleBasedThreatMatchingStrategy


@lru_cache(maxsize=1)
def get_threat_catalog_service() -> ThreatCatalogService:
    """Threat catalog and recommendations from JSON configuration."""
    return ThreatCatalogService(get_config_repository())


@lru_cache(maxsize=1)
def get_risk_context_service() -> RiskContextService:
    """Risk context derived from historical incident intensity."""
    return RiskContextService(get_data_repository())


@lru_cache(maxsize=1)
def get_prediction_service() -> PredictionService:
    """Scoring, catalog, and optional ML stack for /predict* endpoints."""
    repository = get_config_repository()
    scoring_processor = ThreatScoringProcessor(repository.load_scoring_config(), get_risk_context_service())
    return PredictionService(scoring_processor, get_threat_catalog_service(), get_ml_prediction_model_service())


@lru_cache(maxsize=1)
def get_stats_service() -> StatsService:
    """Incident aggregates for GET /stats."""
    return StatsService(get_data_repository())


@lru_cache(maxsize=1)
def get_vulnerability_mapping_service() -> VulnerabilityMappingService:
    """Rule-based mapping of CVEs and assets to catalog threats."""
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


@lru_cache(maxsize=1)
def get_organization_settings_service() -> OrganizationSettingsService:
    """Organization infrastructure settings persistence."""
    return OrganizationSettingsService()


@lru_cache(maxsize=1)
def get_ml_prediction_model_service() -> MlPredictionModelService:
    """CatBoost region-hour model from `ML_ARTIFACTS_DIR` or `models/catboost_region_risk/`; else sklearn RandomForest."""
    return MlPredictionModelService(get_data_repository())
