"""Feature engineering from the notebook, kept compatible with saved model artifacts."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


FEATURE_COLUMNS = [
    "incidents_count",
    "unique_enterprises",
    "unique_threats",
    "avg_host_count",
    "median_host_count",
    "avg_host_count_log",
    "median_host_count_log",
    "threat_danger_score",
    "hour",
    "dayofweek",
    "month",
    "quarter",
    "is_weekend",
    "is_working_hours",
    "is_peak_hours",
    "lag_attack_1",
    "lag_attack_2",
    "lag_attack_3",
    "lag_attack_6",
    "lag_attack_12",
    "lag_attack_24",
    "lag_incidents_1",
    "lag_incidents_2",
    "lag_incidents_3",
    "lag_incidents_6",
    "lag_incidents_12",
    "lag_incidents_24",
    "lag_success_1",
    "lag_success_2",
    "lag_success_3",
    "lag_success_6",
    "lag_success_12",
    "lag_success_24",
    "rolling_attack_mean_6",
    "rolling_attack_mean_24",
    "rolling_incidents_sum_6",
    "rolling_incidents_sum_24",
    "rolling_success_sum_6",
    "rolling_success_sum_24",
    "region",
    "dominant_org_type",
    "dominant_threat_source",
    "dominant_impact_object",
    "season",
    "day_period",
]

CAT_FEATURES = [
    "region",
    "dominant_org_type",
    "dominant_threat_source",
    "dominant_impact_object",
    "season",
    "day_period",
]


def safe_mode(series: pd.Series, default: str = "Неизвестно") -> str:
    s = series.dropna()
    if s.empty:
        return default
    mode = s.mode()
    return mode.iloc[0] if not mode.empty else default


def get_season(month: int) -> str:
    if month in [12, 1, 2]:
        return "winter"
    if month in [3, 4, 5]:
        return "spring"
    if month in [6, 7, 8]:
        return "summer"
    return "autumn"


def get_day_period(hour: int) -> str:
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "day"
    if 18 <= hour <= 23:
        return "evening"
    return "night"


def find_best_threshold_f1(y_true: pd.Series | np.ndarray, y_proba: np.ndarray) -> tuple[float, float]:
    best_thr = 0.5
    best_f1 = -1.0
    for thr in np.arange(0.30, 0.81, 0.02):
        pred = (y_proba >= thr).astype(int)
        score = f1_score(y_true, pred, zero_division=0)
        if score > best_f1:
            best_f1 = float(score)
            best_thr = float(thr)
    return best_thr, best_f1


def build_region_hour_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Notebook-compatible region-hour feature matrix."""
    work = df.copy()
    work["time_hour"] = work["regional_time"].dt.floor("H")

    grouped = work.groupby(["region", "time_hour"]).agg(
        incidents_count=("success", "size"),
        successful_count=("success", "sum"),
        unique_enterprises=("enterprise_code", "nunique"),
        unique_threats=("threat_code", "nunique"),
        avg_host_count=("host_count", "mean"),
        median_host_count=("host_count", "median"),
        dominant_org_type=("org_type", lambda x: safe_mode(x, default="Неизвестно")),
        dominant_threat_source=("threat_source", lambda x: safe_mode(x, default="Неизвестно")),
        dominant_impact_object=("impact_object", lambda x: safe_mode(x, default="Неизвестно")),
    ).reset_index()

    if {
        "confidentiality_violation",
        "integrity_violation",
        "availability_violation",
    }.issubset(work.columns):
        threat_danger = work.groupby(["region", "time_hour"]).apply(
            lambda x: (
                x["confidentiality_violation"].fillna(0).astype(int)
                + x["integrity_violation"].fillna(0).astype(int)
                + x["availability_violation"].fillna(0).astype(int)
            ).max()
        ).reset_index(name="threat_danger_score")
    else:
        threat_danger = work.groupby(["region", "time_hour"])["success"].max().reset_index(name="threat_danger_score")

    grouped = grouped.merge(threat_danger, on=["region", "time_hour"], how="left")
    grouped["threat_danger_score"] = grouped["threat_danger_score"].fillna(0)
    grouped["attack_present"] = (grouped["successful_count"] > 0).astype(int)

    all_regions = grouped["region"].dropna().unique().tolist()
    min_time = grouped["time_hour"].min()
    max_time = grouped["time_hour"].max()
    full_time_index = pd.date_range(min_time, max_time, freq="H")
    full_grid = pd.MultiIndex.from_product([all_regions, full_time_index], names=["region", "time_hour"]).to_frame(
        index=False
    )
    full_df = full_grid.merge(grouped, on=["region", "time_hour"], how="left")

    for col in ["incidents_count", "successful_count", "unique_enterprises", "unique_threats"]:
        full_df[col] = full_df[col].fillna(0)
    full_df["avg_host_count"] = full_df.groupby("region")["avg_host_count"].transform(lambda x: x.fillna(x.median()))
    full_df["median_host_count"] = full_df.groupby("region")["median_host_count"].transform(
        lambda x: x.fillna(x.median())
    )
    full_df["avg_host_count"] = full_df["avg_host_count"].fillna(full_df["avg_host_count"].median())
    full_df["median_host_count"] = full_df["median_host_count"].fillna(full_df["median_host_count"].median())

    for col in ["dominant_org_type", "dominant_threat_source", "dominant_impact_object"]:
        full_df[col] = full_df.groupby("region")[col].transform(lambda x: x.fillna(safe_mode(x, default="Неизвестно")))
        full_df[col] = full_df[col].fillna("Неизвестно")

    full_df["threat_danger_score"] = full_df["threat_danger_score"].fillna(0)
    full_df["attack_present"] = full_df["attack_present"].fillna(0).astype(int)

    full_df["hour"] = full_df["time_hour"].dt.hour
    full_df["dayofweek"] = full_df["time_hour"].dt.dayofweek
    full_df["month"] = full_df["time_hour"].dt.month
    full_df["quarter"] = full_df["time_hour"].dt.quarter
    full_df["is_weekend"] = (full_df["dayofweek"] >= 5).astype(int)
    full_df["is_working_hours"] = full_df["hour"].between(9, 18).astype(int)
    full_df["is_peak_hours"] = full_df["hour"].isin([10, 11, 14, 15, 16, 17]).astype(int)
    full_df["season"] = full_df["month"].apply(get_season)
    full_df["day_period"] = full_df["hour"].apply(get_day_period)

    full_df = full_df.sort_values(["region", "time_hour"]).reset_index(drop=True)

    for lag in [1, 2, 3, 6, 12, 24]:
        full_df[f"lag_attack_{lag}"] = full_df.groupby("region")["attack_present"].shift(lag).fillna(0)
        full_df[f"lag_incidents_{lag}"] = full_df.groupby("region")["incidents_count"].shift(lag).fillna(0)
        full_df[f"lag_success_{lag}"] = full_df.groupby("region")["successful_count"].shift(lag).fillna(0)

    full_df["rolling_attack_mean_6"] = (
        full_df.groupby("region")["attack_present"].shift(1).rolling(6, min_periods=1).mean().fillna(0)
    )
    full_df["rolling_attack_mean_24"] = (
        full_df.groupby("region")["attack_present"].shift(1).rolling(24, min_periods=1).mean().fillna(0)
    )
    full_df["rolling_incidents_sum_6"] = (
        full_df.groupby("region")["incidents_count"].shift(1).rolling(6, min_periods=1).sum().fillna(0)
    )
    full_df["rolling_incidents_sum_24"] = (
        full_df.groupby("region")["incidents_count"].shift(1).rolling(24, min_periods=1).sum().fillna(0)
    )
    full_df["rolling_success_sum_6"] = (
        full_df.groupby("region")["successful_count"].shift(1).rolling(6, min_periods=1).sum().fillna(0)
    )
    full_df["rolling_success_sum_24"] = (
        full_df.groupby("region")["successful_count"].shift(1).rolling(24, min_periods=1).sum().fillna(0)
    )

    full_df["avg_host_count_log"] = np.log1p(full_df["avg_host_count"])
    full_df["median_host_count_log"] = np.log1p(full_df["median_host_count"])
    return full_df


def resolve_feature_columns(region_hour_df: pd.DataFrame) -> tuple[list[str], list[str]]:
    feature_cols = [c for c in FEATURE_COLUMNS if c in region_hour_df.columns]
    cat_features = [c for c in CAT_FEATURES if c in feature_cols]
    return feature_cols, cat_features
