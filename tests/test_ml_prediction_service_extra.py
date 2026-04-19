from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from app.schemas import PredictRequest
from app.services.ml_prediction_model_service import MlPredictionModelService, _SklearnBundle


class DummyRepo:
    def __init__(self, incidents: pd.DataFrame, registry: pd.DataFrame):
        self._incidents = incidents
        self._registry = registry

    def load_incidents(self, db=None):
        return self._incidents.copy()

    def load_fstec_registry(self, db=None):
        return self._registry.copy()


class FakePipeline:
    def __init__(self, label: str, proba: list[float]):
        self.label = label
        self.proba = proba

    def predict(self, frame):
        return [self.label]

    def predict_proba(self, frame):
        return [self.proba]


@pytest.fixture
def predict_payload() -> PredictRequest:
    return PredictRequest(
        organization_id="org-001",
        region="Moscow",
        industry="telecom",
        season="winter",
        day_of_week=2,
        hour=9,
        asset_type="vpn_gateway",
        has_external_access=True,
        privileged_accounts_count=12,
        known_vulnerabilities_count=3,
        prefer_ml=True,
    )


def test_ensure_catboost_loads_once(monkeypatch: pytest.MonkeyPatch):
    calls = {"count": 0}

    def fake_load():
        calls["count"] += 1
        return object(), {"threshold": 0.5, "feature_cols": [], "cat_feature_names": []}

    monkeypatch.setattr("app.services.ml_prediction_model_service.load_catboost_artifacts", fake_load)
    service = MlPredictionModelService(DummyRepo(pd.DataFrame(), pd.DataFrame()))
    assert service._ensure_catboost() is True
    assert service._ensure_catboost() is True
    assert calls["count"] == 1


def test_get_region_hour_df_handles_empty_trim_and_cache(monkeypatch: pytest.MonkeyPatch):
    incidents = pd.DataFrame({"x": [1]})
    registry = pd.DataFrame({"threat_code": [1]})
    service = MlPredictionModelService(DummyRepo(incidents, registry))

    merged = pd.DataFrame(
        {
            "region": ["Moscow"] * 3,
            "regional_time": pd.to_datetime(["2025-01-01", "2026-03-01", "2026-03-02"]),
        }
    )
    built = pd.DataFrame({"region": ["Moscow"], "time_hour": pd.to_datetime(["2026-03-02 00:00:00"])})
    monkeypatch.setattr("app.services.ml_prediction_model_service.build_merged_incidents_df", lambda i, r: merged.copy())
    monkeypatch.setattr("app.services.ml_prediction_model_service.build_region_hour_dataset", lambda df: built.copy())

    first = service._get_region_hour_df(db=None)
    second = service._get_region_hour_df(db=None)
    assert first is not None
    assert first.equals(built)
    assert second.equals(built)

    monkeypatch.setattr("app.services.ml_prediction_model_service.build_merged_incidents_df", lambda i, r: pd.DataFrame())
    assert MlPredictionModelService(DummyRepo(incidents, registry))._get_region_hour_df(db=None) is None


def test_resolve_region_and_method_target_from_incidents(predict_payload: PredictRequest):
    service = MlPredictionModelService(DummyRepo(pd.DataFrame(), pd.DataFrame()))
    region_hour_df = pd.DataFrame({"region": ["Perm", "Perm", "Moscow"]})
    assert service._resolve_region(region_hour_df, "Moscow") == "Moscow"
    assert service._resolve_region(region_hour_df, "Unknown") == "Perm"
    assert service._resolve_region(pd.DataFrame({"region": []}), "Unknown") == "Unknown"

    service._build_training_dataset = lambda db=None: pd.DataFrame(
        {
            "organization_code": ["org-001", "org-001", "org-777"],
            "region": ["Moscow", "Moscow", "Perm"],
            "attack_method": ["malware", "malware", "phishing"],
            "target_object": ["file_server", "file_server", "crm"],
        }
    )
    assert service._method_target_from_incidents(predict_payload, None) == ("malware", "file_server")

    service._build_training_dataset = lambda db=None: pd.DataFrame(
        {
            "organization_code": ["org-777", "org-777"],
            "region": ["Moscow", "Moscow"],
            "attack_method": ["phishing", "phishing"],
            "target_object": ["crm", "crm"],
        }
    )
    assert service._method_target_from_incidents(predict_payload, None) == ("phishing", "crm")

    service._build_training_dataset = lambda db=None: pd.DataFrame()
    assert service._method_target_from_incidents(predict_payload, None) == ("brute_force", "vpn_gateway")


def test_predict_catboost_success_and_exception(monkeypatch: pytest.MonkeyPatch, predict_payload: PredictRequest):
    service = MlPredictionModelService(DummyRepo(pd.DataFrame(), pd.DataFrame()))
    service._catboost_model = object()
    service._catboost_meta = {"threshold": 0.5}
    service._get_region_hour_df = lambda db=None: pd.DataFrame({"region": ["Moscow"]})
    service._method_target_from_incidents = lambda payload, db=None: ("malware", "file_server")
    monkeypatch.setattr(
        "app.services.ml_prediction_model_service.predict_region_hour_proba",
        lambda model, meta, rh, region, hour: (0.876, 1),
    )
    result = service._predict_catboost(predict_payload, None)
    assert result is not None
    assert result.attack_method == "malware"
    assert result.target_object == "file_server"
    assert result.confidence == 0.88

    monkeypatch.setattr(
        "app.services.ml_prediction_model_service.predict_region_hour_proba",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert service._predict_catboost(predict_payload, None) is None


def test_predict_returns_none_for_sparse_dataset_and_uses_cached_bundle(predict_payload: PredictRequest):
    service = MlPredictionModelService(DummyRepo(pd.DataFrame(), pd.DataFrame()))
    service._ensure_catboost = lambda: False
    service._build_training_dataset = lambda db=None: pd.DataFrame({"organization_code": ["org-001"] * 9})
    assert service.predict(predict_payload, None) is None

    rich = pd.DataFrame(
        {
            "organization_code": ["org-001"] * 10 + ["org-999"] * 2,
            "region": ["Moscow"] * 12,
            "industry": ["telecom"] * 12,
            "season": ["winter"] * 12,
            "day_of_week": [2] * 12,
            "hour": list(range(12)),
            "has_external_access": ["True"] * 12,
            "privileged_accounts_count": [12] * 12,
            "known_vulnerabilities_count": [3] * 12,
            "attack_method": ["malware"] * 12,
            "target_object": ["file_server"] * 12,
        }
    )
    service._build_training_dataset = lambda db=None: rich.copy()
    bundle = _SklearnBundle(
        method_pipeline=FakePipeline("malware", [0.2, 0.8]),
        target_pipeline=FakePipeline("file_server", [0.1, 0.9]),
        row_count=10,
    )
    calls = {"count": 0}

    def fake_get_or_train(dataset):
        calls["count"] += 1
        assert len(dataset) == 10
        return bundle

    service._get_or_train_sklearn_bundle = fake_get_or_train
    result = service.predict(predict_payload, None)
    assert result is not None
    assert result.attack_method == "malware"
    assert result.target_object == "file_server"
    assert result.confidence == 0.85
    assert calls["count"] == 1


def test_get_or_train_sklearn_bundle_reuses_cache():
    service = MlPredictionModelService(DummyRepo(pd.DataFrame(), pd.DataFrame()))
    dataset = pd.DataFrame(
        {
            "organization_code": ["org-001"] * 10,
            "region": ["Moscow"] * 10,
            "industry": ["telecom"] * 10,
            "season": ["winter"] * 10,
            "day_of_week": [2] * 10,
            "hour": list(range(10)),
            "has_external_access": ["True"] * 10,
            "privileged_accounts_count": [10] * 10,
            "known_vulnerabilities_count": [2] * 10,
            "attack_method": ["malware"] * 10,
            "target_object": ["file_server"] * 10,
        }
    )
    first = service._get_or_train_sklearn_bundle(dataset)
    second = service._get_or_train_sklearn_bundle(dataset)
    assert first is second


def test_build_training_dataset_empty_and_happy_path():
    incidents = pd.DataFrame(
        {
            "organization_code": ["org-001", "org-001", "org-002"],
            "region": ["Moscow", "Moscow", "Perm"],
            "industry": ["telecom", "telecom", "finance"],
            "season": ["winter", "winter", "winter"],
            "day_of_week": [2, 3, 4],
            "hour": [9, 10, 11],
            "host_count": [100, 40, 60],
            "threat_code": [101, 101, 102],
        }
    )
    registry = pd.DataFrame(
        {
            "threat_code": [101, 102],
            "name": ["Phishing email", "SQL exploit"],
            "description": ["phishing in mail", "sql injection app"],
            "object_of_impact": ["почта", "субд"],
        }
    )
    service = MlPredictionModelService(DummyRepo(incidents, registry))
    dataset = service._build_training_dataset()
    assert set(["attack_method", "target_object", "known_vulnerabilities_count"]).issubset(dataset.columns)
    assert dataset["known_vulnerabilities_count"].max() >= 1
    assert dataset["privileged_accounts_count"].min() >= 1
    assert dataset["has_external_access"].isin(["True", "False"]).all()

    empty_registry = pd.DataFrame(columns=["threat_code", "name", "description", "object_of_impact"])
    empty_service = MlPredictionModelService(DummyRepo(pd.DataFrame(), empty_registry))
    assert empty_service._build_training_dataset().empty
