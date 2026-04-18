"""Region-risk CatBoost pipeline used by notebook training and backend inference."""

from app.ml.region_risk.artifacts import (
    default_artifacts_dir,
    load_catboost_artifacts,
    save_catboost_artifacts,
)
from app.ml.region_risk.features import build_region_hour_dataset
from app.ml.region_risk.inference import build_region_hour_prediction_rows, predict_region_hour_proba
from app.ml.region_risk.loader import (
    DEFAULT_INCIDENTS_PATH,
    DEFAULT_THREATLIST_PATH,
    build_merged_incidents_df,
    prepare_data_from_paths,
)
from app.ml.region_risk.trainer import train_region_risk_model

__all__ = [
    "DEFAULT_INCIDENTS_PATH",
    "DEFAULT_THREATLIST_PATH",
    "build_merged_incidents_df",
    "prepare_data_from_paths",
    "build_region_hour_dataset",
    "train_region_risk_model",
    "default_artifacts_dir",
    "load_catboost_artifacts",
    "save_catboost_artifacts",
    "build_region_hour_prediction_rows",
    "predict_region_hour_proba",
]
