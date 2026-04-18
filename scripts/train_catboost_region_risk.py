#!/usr/bin/env python3
"""Train CatBoost region-hour model from DB or Excel incidents + FSTEC registry; write models/catboost_region_risk/."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.ml.region_risk.artifacts import default_artifacts_dir, save_catboost_artifacts
from app.ml.region_risk.features import build_region_hour_dataset
from app.ml.region_risk.loader import build_merged_incidents_df, prepare_data_from_paths
from app.ml.region_risk.trainer import train_region_risk_model
from app.repositories.data_repository import DataRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="Train CatBoost region-hour risk model.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for region_risk.cbm and metadata.json (default: models/catboost_region_risk)",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Use Excel/file fallback from DataRepository instead of PostgreSQL",
    )
    parser.add_argument(
        "--max-train-rows",
        type=int,
        default=50_000,
        help="Cap training rows (chronological tail) when the region-hour grid is huge (default: 50000)",
    )
    args = parser.parse_args()
    out = args.output_dir or default_artifacts_dir()

    repo = DataRepository()
    if args.no_db:
        merged = prepare_data_from_paths()
    else:
        with SessionLocal() as db:
            incidents = repo.load_incidents(db=db)
            registry = repo.load_fstec_registry(db=db)
        merged = build_merged_incidents_df(incidents, registry)
    if merged.empty:
        print("No incident rows after merge; seed the DB or point to incidents Excel.", file=sys.stderr)
        return 1

    rh = build_region_hour_dataset(merged)
    print(f"region_hour_df: {rh.shape}, target mean={rh['attack_present'].mean():.4f}")

    try:
        artifacts = train_region_risk_model(rh, max_train_rows=args.max_train_rows)
        save_catboost_artifacts(
            artifacts.model,
            artifacts.features,
            artifacts.cat_features,
            artifacts.threshold,
            output_dir=out,
        )
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    print(f"Artifacts written under {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
