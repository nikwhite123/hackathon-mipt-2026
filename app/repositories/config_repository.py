from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas import RuleConfig, ScoringConfig, ThreatCatalogConfig

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"


class ConfigRepository:
    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir

    def _read_json(self, filename: str) -> dict:
        path = self.config_dir / filename
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def load_scoring_config(self) -> ScoringConfig:
        return ScoringConfig.model_validate(self._read_json("scoring.json"))

    def load_threat_catalog(self) -> ThreatCatalogConfig:
        return ThreatCatalogConfig.model_validate(self._read_json("threat_catalog.json"))

    def load_mapping_rules(self) -> list[RuleConfig]:
        raw_rules = self._read_json("mapping_rules.json")
        return [RuleConfig.model_validate(rule) for rule in raw_rules]


@lru_cache(maxsize=1)
def get_config_repository() -> ConfigRepository:
    return ConfigRepository()
