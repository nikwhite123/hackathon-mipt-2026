"""Persist and load CatBoost artifacts for backend inference."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from catboost import CatBoostClassifier

BASE_DIR = Path(__file__).resolve().parents[3]


def default_artifacts_dir() -> Path:
    override = os.getenv("ML_ARTIFACTS_DIR")
    if override:
        return Path(override).expanduser()
    return BASE_DIR / "models" / "catboost_region_risk"


def save_catboost_artifacts(
    model: CatBoostClassifier,
    feature_cols: list[str],
    cat_feature_names: list[str],
    threshold: float,
    *,
    output_dir: Path | None = None,
) -> Path:
    out = output_dir or default_artifacts_dir()
    out.mkdir(parents=True, exist_ok=True)
    model.save_model(str(out / "region_risk.cbm"))
    (out / "metadata.json").write_text(
        json.dumps(
            {
                "feature_cols": feature_cols,
                "cat_feature_names": cat_feature_names,
                "threshold": float(threshold),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return out


def load_catboost_artifacts(output_dir: Path | None = None) -> tuple[CatBoostClassifier, dict[str, Any]] | tuple[None, None]:
    out = output_dir or default_artifacts_dir()
    model_path = out / "region_risk.cbm"
    metadata_path = out / "metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        return None, None

    model = CatBoostClassifier()
    model.load_model(str(model_path))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    return model, metadata
