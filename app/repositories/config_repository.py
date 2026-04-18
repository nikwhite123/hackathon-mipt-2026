"""Read JSON configs: scoring, threat_catalog, and mapping_rules."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas import RuleConfig, ScoringConfig, ThreatCatalogConfig

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


class ConfigRepository:
    """Parse JSON files under config/."""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir

    def _read_json(self, filename: str) -> dict:
        """Read UTF-8 JSON and return a dict."""
        path = self.config_dir / filename
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_scoring_config(self) -> ScoringConfig:
        return _validate_model(ScoringConfig, self._read_json("scoring.json"))

    def load_threat_catalog(self) -> ThreatCatalogConfig:
        return _validate_model(ThreatCatalogConfig, self._read_json("threat_catalog.json"))

    def load_mapping_rules(self) -> list[RuleConfig]:
        raw_rules = self._read_json("mapping_rules.json")
        return [_validate_model(RuleConfig, rule) for rule in raw_rules]


@lru_cache(maxsize=1)
def get_config_repository() -> ConfigRepository:
    """Process-wide singleton ConfigRepository."""
    return ConfigRepository()


def _validate_model(model_cls, payload):
    """Unified parse: pydantic v2 model_validate or v1 parse_obj."""
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(payload)
    return model_cls.parse_obj(payload)
