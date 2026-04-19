from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from app.ml.region_risk import artifacts as artifacts_mod
from app.ml.region_risk import features as features_mod
from app.ml.region_risk import inference as inference_mod
from app.ml.region_risk import loader as loader_mod
from app.ml.region_risk import trainer as trainer_mod
from app.schemas import (
    RuleConfig,
    ScoringConfig,
    ThreatCatalogConfig,
    ThreatReference,
    ProtectionRecommendation,
    UserRegisterRequest,
)


class DummyCatBoostModel:
    def __init__(self):
        self.saved_path = None
        self.loaded_path = None

    def save_model(self, path: str):
        self.saved_path = path
        Path(path).write_text("dummy-model", encoding="utf-8")

    def load_model(self, path: str):
        self.loaded_path = path

    def predict_proba(self, pool):
        return np.array([[0.25, 0.75]])


class DummyPool:
    def __init__(self, data, label=None, cat_features=None):
        self.data = data
        self.label = label
        self.cat_features = cat_features


def make_region_hour_df() -> pd.DataFrame:
    base = pd.Timestamp("2026-01-01 00:00:00")
    rows = []
    for idx in range(30):
        rows.append(
            {
                "region": "Moscow",
                "time_hour": base + pd.Timedelta(hours=idx),
                "incidents_count": 1 + (idx % 3),
                "successful_count": idx % 2,
                "unique_enterprises": 2,
                "unique_threats": 1,
                "avg_host_count": 100.0,
                "median_host_count": 90.0,
                "dominant_org_type": "telecom",
                "dominant_threat_source": "external",
                "dominant_impact_object": "vpn",
                "threat_danger_score": 1.0,
                "attack_present": idx % 2,
                "hour": (base + pd.Timedelta(hours=idx)).hour,
                "dayofweek": (base + pd.Timedelta(hours=idx)).dayofweek,
                "month": (base + pd.Timedelta(hours=idx)).month,
                "quarter": (base + pd.Timedelta(hours=idx)).quarter,
                "season": "winter",
                "day_period": "night",
            }
        )
    return pd.DataFrame(rows)


def test_artifacts_default_dir_respects_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setenv("ML_ARTIFACTS_DIR", str(tmp_path))
    assert artifacts_mod.default_artifacts_dir() == tmp_path


def test_artifacts_save_and_load_roundtrip(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(artifacts_mod, "CatBoostClassifier", DummyCatBoostModel)
    model = DummyCatBoostModel()
    out_dir = artifacts_mod.save_catboost_artifacts(
        model,
        ["region", "hour"],
        ["region"],
        0.61,
        output_dir=tmp_path,
    )
    assert out_dir == tmp_path
    metadata_path = tmp_path / "metadata.json"
    assert metadata_path.exists()
    loaded_model, metadata = artifacts_mod.load_catboost_artifacts(tmp_path)
    assert isinstance(loaded_model, DummyCatBoostModel)
    assert loaded_model.loaded_path.endswith("region_risk.cbm")
    assert metadata["threshold"] == 0.61
    assert metadata["feature_cols"] == ["region", "hour"]


def test_artifacts_load_returns_none_when_files_missing(tmp_path):
    assert artifacts_mod.load_catboost_artifacts(tmp_path) == (None, None)


def test_safe_mode_and_calendar_helpers_cover_edges():
    assert features_mod.safe_mode(pd.Series([None, np.nan]), default="fallback") == "fallback"
    assert features_mod.safe_mode(pd.Series(["b", "a", "a"])) == "a"
    assert features_mod.get_season(12) == "winter"
    assert features_mod.get_season(4) == "spring"
    assert features_mod.get_season(7) == "summer"
    assert features_mod.get_season(10) == "autumn"
    assert features_mod.get_day_period(6) == "morning"
    assert features_mod.get_day_period(12) == "day"
    assert features_mod.get_day_period(18) == "evening"
    assert features_mod.get_day_period(3) == "night"


def test_find_best_threshold_f1_and_resolve_feature_columns():
    y_true = np.array([0, 1, 1, 0, 1])
    y_proba = np.array([0.1, 0.9, 0.8, 0.2, 0.7])
    thr, f1 = features_mod.find_best_threshold_f1(y_true, y_proba)
    assert 0.30 <= thr <= 0.80
    assert 0.9 <= f1 <= 1.0

    frame = pd.DataFrame(columns=["region", "hour", "day_period", "unknown"])
    feature_cols, cat_features = features_mod.resolve_feature_columns(frame)
    assert feature_cols == ["hour", "region", "day_period"] or feature_cols == ["region", "hour", "day_period"]
    assert set(cat_features) == {"region", "day_period"}


def test_build_region_hour_dataset_with_and_without_violation_columns():
    df = pd.DataFrame(
        {
            "region": ["Moscow", "Moscow"],
            "regional_time": pd.to_datetime(["2026-01-01 09:10", "2026-01-01 10:20"]),
            "success": [1, 0],
            "enterprise_code": ["e1", "e2"],
            "threat_code": [10, 20],
            "host_count": [100, 200],
            "org_type": ["telecom", None],
            "threat_source": ["external", None],
            "impact_object": ["vpn", None],
            "confidentiality_violation": [1, 0],
            "integrity_violation": [0, 1],
            "availability_violation": [0, 0],
        }
    )
    dataset = features_mod.build_region_hour_dataset(df)
    assert not dataset.empty
    assert "rolling_attack_mean_24" in dataset.columns
    assert dataset["attack_present"].max() == 1
    assert dataset["threat_danger_score"].max() >= 1

    dataset_no_violation = features_mod.build_region_hour_dataset(df.drop(columns=["confidentiality_violation", "integrity_violation", "availability_violation"]))
    assert "threat_danger_score" in dataset_no_violation.columns
    assert dataset_no_violation["threat_danger_score"].max() in {0, 1}


def test_inference_build_prediction_rows_for_existing_and_missing_region():
    region_hour_df = make_region_hour_df()
    rows_existing = inference_mod.build_region_hour_prediction_rows(region_hour_df, "Moscow", date(2026, 1, 3))
    rows_missing = inference_mod.build_region_hour_prediction_rows(region_hour_df, "Perm", date(2026, 1, 3))

    assert len(rows_existing) == 24
    assert len(rows_missing) == 24
    assert set(rows_existing["hour"]) == set(range(24))
    assert rows_missing["dominant_org_type"].nunique() == 1
    assert (rows_existing["avg_host_count_log"] > 0).all()


def test_predict_region_hour_proba_uses_fallback_first_row(monkeypatch: pytest.MonkeyPatch):
    region_hour_df = make_region_hour_df()
    captured = {}

    def fake_pool(data, cat_features=None):
        captured["columns"] = list(data.columns)
        captured["cat_features"] = list(cat_features)
        return SimpleNamespace(data=data)

    monkeypatch.setattr(inference_mod, "Pool", fake_pool)
    model = DummyCatBoostModel()
    proba, predicted = inference_mod.predict_region_hour_proba(
        model,
        {"feature_cols": ["region", "hour", "missing_feature"], "cat_feature_names": ["region"], "threshold": 0.5},
        region_hour_df,
        "Moscow",
        hour=99,
        target_date=date(2026, 1, 3),
    )
    assert proba == 0.75
    assert predicted == 1
    assert captured["columns"] == ["region", "hour", "missing_feature"]
    assert captured["cat_features"] == [0]


def test_loader_normalize_columns_and_build_merged_incidents_df():
    normalized = loader_mod.normalize_columns(pd.Index(["  a   b  ", " c"]))
    assert normalized == ["a b", "c"]

    incidents = pd.DataFrame(
        {
            "industry": [" telecom ", "finance"],
            "organization_code": [" org-1 ", "org-2"],
            "host_count": [100, "bad"],
            "threat_code": [101, 102],
            "success": [1, 2],
            "region": [" Moscow ", "Perm"],
            "regional_time": ["01.02.2026 10:00", None],
        }
    )
    registry = pd.DataFrame(
        {
            "threat_code": [101, 101],
            "name": ["Threat A", "Threat A duplicate"],
            "source_characteristics": ["external", "external"],
            "object_of_impact": ["vpn", "vpn"],
            "confidentiality_breach": [1, 0],
            "integrity_breach": [0, 0],
            "availability_breach": [0, 0],
            "description": ["desc", "desc2"],
        }
    )
    merged = loader_mod.build_merged_incidents_df(incidents, registry)
    assert len(merged) == 1
    assert merged.iloc[0]["org_type"] == "telecom"
    assert merged.iloc[0]["enterprise_code"] == "org-1"
    assert merged.iloc[0]["threat_name"] == "Threat A"
    assert merged.iloc[0]["confidentiality_violation"] == 1


def test_loader_build_merged_incidents_df_returns_empty_for_empty_incidents():
    incidents = pd.DataFrame(columns=["organization_code", "industry"])
    registry = pd.DataFrame(columns=["threat_code"])
    merged = loader_mod.build_merged_incidents_df(incidents, registry)
    assert merged.empty


def test_read_table_raises_for_bad_manual_columns(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        loader_mod.read_table(path, no_header=True, manual_columns=["x"])


def test_read_incident_and_threat_sheet_find_shifted_header(monkeypatch: pytest.MonkeyPatch):
    incidents_raw = pd.DataFrame(
        [
            ["noise"] * len(loader_mod.INCIDENTS_COLUMNS),
            loader_mod.INCIDENTS_COLUMNS,
            ["telecom", "org-1", 100, 101, 1, "Moscow", "01.01.2026", "01.01.2026 09:00"],
        ]
    )
    threat_raw = pd.DataFrame(
        [
            ["noise"] * len(loader_mod.THREAT_COLUMNS),
            ["noise"] * len(loader_mod.THREAT_COLUMNS),
            loader_mod.THREAT_COLUMNS,
            [101, "Threat", "Desc", "external", "vpn", 1, 0, 0, None, None, None, None],
        ]
    )
    monkeypatch.setattr(loader_mod, "read_table", lambda path, no_header=True: incidents_raw)
    assert not loader_mod._read_incidents_sheet(SimpleNamespace(name="inc.xlsx")).empty
    monkeypatch.setattr(loader_mod, "read_table", lambda path, no_header=True: threat_raw)
    assert not loader_mod._read_threat_sheet(SimpleNamespace(name="thr.xlsx")).empty


class FakeTrainModel:
    def __init__(self, **params):
        self.params = params

    def fit(self, train_pool, eval_set=None, early_stopping_rounds=None, use_best_model=None, verbose=None):
        return self

    def predict_proba(self, X):
        if hasattr(X, "__len__"):
            n = len(X)
        else:
            n = 1
        values = np.linspace(0.2, 0.8, num=max(n, 1))
        return np.column_stack([1 - values, values])


def test_manual_param_search_and_optuna_fallback(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(trainer_mod, "CatBoostClassifier", FakeTrainModel)
    monkeypatch.setattr(trainer_mod, "Pool", DummyPool)
    X_train = pd.DataFrame({"region": ["A"] * 8, "hour": list(range(8))})
    y_train = pd.Series([0, 1, 0, 1, 0, 1, 0, 1])
    X_val = pd.DataFrame({"region": ["A"] * 4, "hour": [8, 9, 10, 11]})
    y_val = pd.Series([0, 1, 0, 1])
    params = trainer_mod._manual_param_search(X_train, y_train, X_val, y_val, [0])
    assert params["loss_function"] == "Logloss"
    monkeypatch.setitem(__import__("sys").modules, "optuna", None)
    fallback = trainer_mod.optimize_model_with_optuna(X_train, y_train, X_val, y_val, [0])
    assert fallback["eval_metric"] == "F1"


def test_train_region_risk_model_with_patched_components(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(trainer_mod, "CatBoostClassifier", FakeTrainModel)
    monkeypatch.setattr(trainer_mod, "Pool", DummyPool)
    monkeypatch.setattr(trainer_mod, "TimeSeriesSplit", lambda n_splits: SimpleNamespace(split=lambda X: [
        (np.arange(0, 12), np.arange(12, 16)),
        (np.arange(0, 16), np.arange(16, 20)),
        (np.arange(0, 16), np.arange(16, 20)),
    ]))
    monkeypatch.setattr(trainer_mod, "roc_auc_score", lambda y_true, y_score: 0.73)

    region_hour_df = make_region_hour_df().iloc[:24].copy()
    artifacts = trainer_mod.train_region_risk_model(region_hour_df, use_optuna=False, max_train_rows=20)
    assert artifacts.threshold >= 0.30
    assert len(artifacts.features) >= 5
    assert len(artifacts.cv_results) == 3
    assert len(artifacts.region_hour_df) == 20


def test_schema_validators_cover_password_rule_configs_and_catalog():
    user = UserRegisterRequest(
        first_name="  Ivan ",
        last_name=" Petrov ",
        email="  IVAN@example.com ",
        password="Secret12345",
        organization_code=" org-001 ",
    )
    assert user.first_name == "Ivan"
    assert user.email == "ivan@example.com"
    assert user.organization_code == "org-001"

    with pytest.raises(ValidationError):
        RuleConfig(tokens=[], threat_id="TH-1", match_score=0.5, reason="x", recommendation_method="malware")

    with pytest.raises(ValidationError):
        ScoringConfig(
            vulnerability_count_weight=1,
            attack_intensity_weight=1,
            asset_criticality_weight=1,
            risk_score_normalizer=10,
            confidence_base=0.1,
            confidence_multiplier=0.5,
            asset_criticality_by_target={"crm": -1},
        )

    threat = ThreatReference(
        threat_id="TH-1",
        name="Threat",
        description="Desc",
        category="cat",
        severity="high",
        likely_targets=["crm"],
        common_methods=["malware"],
    )
    rec = ProtectionRecommendation(code="R1", title="Do", description="Desc", priority=1)
    with pytest.raises(ValidationError):
        ThreatCatalogConfig(threats=[threat], recommendations={"unknown": [rec]})
