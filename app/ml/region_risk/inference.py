"""Inference helpers that build the same feature rows used during notebook training."""

from __future__ import annotations

from datetime import date, datetime

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, Pool

from app.ml.region_risk.features import get_day_period, get_season, safe_mode


def build_region_hour_prediction_rows(
    region_hour_df: pd.DataFrame,
    region: str,
    target_date: date | datetime | pd.Timestamp,
) -> pd.DataFrame:
    target_date = pd.Timestamp(target_date).normalize()
    reg_hist = region_hour_df[region_hour_df["region"] == region].copy()

    if reg_hist.empty:
        base_org = safe_mode(region_hour_df["dominant_org_type"], default="Неизвестно")
        base_src = safe_mode(region_hour_df["dominant_threat_source"], default="Неизвестно")
        base_obj = safe_mode(region_hour_df["dominant_impact_object"], default="Неизвестно")
        avg_host = float(region_hour_df["avg_host_count"].median())
        med_host = float(region_hour_df["median_host_count"].median())
        danger = float(region_hour_df["threat_danger_score"].median())
        hist = pd.DataFrame()
    else:
        reg_hist = reg_hist.sort_values("time_hour").copy()
        base_org = safe_mode(reg_hist["dominant_org_type"], default="Неизвестно")
        base_src = safe_mode(reg_hist["dominant_threat_source"], default="Неизвестно")
        base_obj = safe_mode(reg_hist["dominant_impact_object"], default="Неизвестно")
        avg_host = float(reg_hist["avg_host_count"].median())
        med_host = float(reg_hist["median_host_count"].median())
        danger = float(reg_hist["threat_danger_score"].median())
        hist = reg_hist.copy()

    rows: list[dict[str, object]] = []
    for hour in range(24):
        dt = target_date + pd.Timedelta(hours=hour)
        h = hist[hist["time_hour"] < dt].sort_values("time_hour").copy() if not hist.empty else pd.DataFrame()

        def get_lag(col: str, lag: int, default: float = 0) -> float:
            if h.empty or col not in h.columns or len(h) < lag:
                return default
            return float(h[col].iloc[-lag]) if len(h) >= lag else default

        rows.append(
            {
                "region": region,
                "time_hour": dt,
                "incidents_count": float(h["incidents_count"].tail(6).mean())
                if ("incidents_count" in h.columns and not h.empty and len(h) > 0)
                else 0,
                "unique_enterprises": float(h["unique_enterprises"].tail(6).mean())
                if ("unique_enterprises" in h.columns and not h.empty and len(h) > 0)
                else 0,
                "unique_threats": float(h["unique_threats"].tail(6).mean())
                if ("unique_threats" in h.columns and not h.empty and len(h) > 0)
                else 0,
                "avg_host_count": avg_host,
                "median_host_count": med_host,
                "avg_host_count_log": float(np.log1p(avg_host)),
                "median_host_count_log": float(np.log1p(med_host)),
                "threat_danger_score": danger,
                "hour": dt.hour,
                "dayofweek": dt.dayofweek,
                "month": dt.month,
                "quarter": dt.quarter,
                "is_weekend": int(dt.dayofweek >= 5),
                "is_working_hours": int(9 <= dt.hour <= 18),
                "is_peak_hours": int(dt.hour in [10, 11, 14, 15, 16, 17]),
                "dominant_org_type": base_org,
                "dominant_threat_source": base_src,
                "dominant_impact_object": base_obj,
                "season": get_season(dt.month),
                "day_period": get_day_period(dt.hour),
                "lag_attack_1": get_lag("attack_present", 1, 0),
                "lag_attack_2": get_lag("attack_present", 2, 0),
                "lag_attack_3": get_lag("attack_present", 3, 0),
                "lag_attack_6": get_lag("attack_present", 6, 0),
                "lag_attack_12": get_lag("attack_present", 12, 0),
                "lag_attack_24": get_lag("attack_present", 24, 0),
                "lag_incidents_1": get_lag("incidents_count", 1, 0),
                "lag_incidents_2": get_lag("incidents_count", 2, 0),
                "lag_incidents_3": get_lag("incidents_count", 3, 0),
                "lag_incidents_6": get_lag("incidents_count", 6, 0),
                "lag_incidents_12": get_lag("incidents_count", 12, 0),
                "lag_incidents_24": get_lag("incidents_count", 24, 0),
                "lag_success_1": get_lag("successful_count", 1, 0),
                "lag_success_2": get_lag("successful_count", 2, 0),
                "lag_success_3": get_lag("successful_count", 3, 0),
                "lag_success_6": get_lag("successful_count", 6, 0),
                "lag_success_12": get_lag("successful_count", 12, 0),
                "lag_success_24": get_lag("successful_count", 24, 0),
                "rolling_attack_mean_6": float(h["attack_present"].tail(6).mean())
                if ("attack_present" in h.columns and not h.empty and len(h) >= 6)
                else 0,
                "rolling_attack_mean_24": float(h["attack_present"].tail(24).mean())
                if ("attack_present" in h.columns and not h.empty and len(h) >= 24)
                else 0,
                "rolling_incidents_sum_6": float(h["incidents_count"].tail(6).sum())
                if ("incidents_count" in h.columns and not h.empty and len(h) >= 6)
                else 0,
                "rolling_incidents_sum_24": float(h["incidents_count"].tail(24).sum())
                if ("incidents_count" in h.columns and not h.empty and len(h) >= 24)
                else 0,
                "rolling_success_sum_6": float(h["successful_count"].tail(6).sum())
                if ("successful_count" in h.columns and not h.empty and len(h) >= 6)
                else 0,
                "rolling_success_sum_24": float(h["successful_count"].tail(24).sum())
                if ("successful_count" in h.columns and not h.empty and len(h) >= 24)
                else 0,
            }
        )

    return pd.DataFrame(rows)


def predict_region_hour_proba(
    model: CatBoostClassifier,
    metadata: dict[str, object],
    region_hour_df: pd.DataFrame,
    region: str,
    *,
    hour: int,
    target_date: date | datetime | pd.Timestamp | None = None,
) -> tuple[float, int]:
    if target_date is None:
        target_date = pd.Timestamp.now().normalize()
    pred_df = build_region_hour_prediction_rows(region_hour_df, region, target_date)
    feature_cols = list(metadata["feature_cols"])
    cat_feature_names = list(metadata["cat_feature_names"])
    row = pred_df[pred_df["hour"] == hour]
    if row.empty:
        row = pred_df.iloc[[0]].copy()
    for feature in feature_cols:
        if feature not in row.columns:
            row[feature] = 0
    cat_idx = [feature_cols.index(c) for c in cat_feature_names if c in feature_cols]
    pool = Pool(row[feature_cols], cat_features=cat_idx)
    proba = float(model.predict_proba(pool)[0, 1])
    threshold = float(metadata["threshold"])
    return proba, int(proba >= threshold)
