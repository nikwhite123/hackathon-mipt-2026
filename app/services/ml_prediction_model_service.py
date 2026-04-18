"""Train and run ML on incidents: CatBoost region-hour risk (preferred) or sklearn RandomForest method/target."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session

from app.ml.region_risk.artifacts import load_catboost_artifacts
from app.ml.region_risk.features import build_region_hour_dataset
from app.ml.region_risk.inference import predict_region_hour_proba
from app.ml.region_risk.loader import build_merged_incidents_df

_INFERENCE_INCIDENT_LOOKBACK_DAYS = 90
_INFERENCE_REGION_HOUR_MAX_ROWS = 50_000
from app.repositories.data_repository import DataRepository
from app.schemas import PredictRequest
from app.services.analytics_service import AnalyticsService


@dataclass
class MlPredictionResult:
    """ML branch output: method, target, confidence, and rationale strings."""

    attack_method: str
    target_object: str
    confidence: float
    rationale: list[str]


@dataclass
class _SklearnBundle:
    """Caches method/target pipelines and the training row count."""

    method_pipeline: Pipeline
    target_pipeline: Pipeline
    row_count: int


class MlPredictionModelService:
    """CatBoost temporal risk when artifacts exist; else RandomForest method/target on incidents."""

    def __init__(self, repository: DataRepository):
        self.repository = repository
        self.analytics_service = AnalyticsService(repository)
        self._sklearn_bundle: _SklearnBundle | None = None
        self._catboost_loaded = False
        self._catboost_model = None
        self._catboost_meta: dict | None = None
        self._region_hour_cache: tuple[int, pd.DataFrame | None] | None = None

    def _ensure_catboost(self) -> bool:
        if self._catboost_loaded:
            return self._catboost_model is not None
        self._catboost_loaded = True
        model, meta = load_catboost_artifacts()
        self._catboost_model, self._catboost_meta = model, meta
        return model is not None

    def _get_region_hour_df(self, db: Session | None) -> pd.DataFrame | None:
        incidents = self.repository.load_incidents(db=db)
        registry = self.repository.load_fstec_registry(db=db)
        merged = build_merged_incidents_df(incidents, registry)
        if merged.empty:
            return None
        if "regional_time" in merged.columns and merged["regional_time"].notna().any():
            cutoff = merged["regional_time"].max() - pd.Timedelta(days=_INFERENCE_INCIDENT_LOOKBACK_DAYS)
            merged = merged[merged["regional_time"] >= cutoff].copy()
        if merged.empty:
            return None
        rh = build_region_hour_dataset(merged)
        if len(rh) > _INFERENCE_REGION_HOUR_MAX_ROWS:
            rh = rh.sort_values(["region", "time_hour"]).tail(_INFERENCE_REGION_HOUR_MAX_ROWS).reset_index(drop=True)
        key = len(merged)
        if self._region_hour_cache and self._region_hour_cache[0] == key:
            return self._region_hour_cache[1]
        self._region_hour_cache = (key, rh)
        return rh

    def _resolve_region(self, region_hour_df: pd.DataFrame, region: str) -> str:
        regions = region_hour_df["region"].dropna().unique()
        if region in regions:
            return region
        if len(regions):
            return str(region_hour_df["region"].mode().iloc[0])
        return region

    def _method_target_from_incidents(self, payload: PredictRequest, db: Session | None) -> tuple[str, str]:
        dataset = self._build_training_dataset(db)
        org_code = str(payload.organization_id)
        if not dataset.empty:
            org_df = dataset[dataset["organization_code"] == org_code]
            if len(org_df) >= 1:
                return (
                    str(org_df["attack_method"].value_counts().idxmax()),
                    str(org_df["target_object"].value_counts().idxmax()),
                )
            reg_df = dataset[dataset["region"] == str(payload.region)]
            if len(reg_df) >= 1:
                return (
                    str(reg_df["attack_method"].value_counts().idxmax()),
                    str(reg_df["target_object"].value_counts().idxmax()),
                )
        from app.services.prediction_service import PredictionService

        return PredictionService._detect_attack_method(str(payload.asset_type)), str(payload.asset_type)

    def _predict_catboost(self, payload: PredictRequest, db: Session | None) -> MlPredictionResult | None:
        assert self._catboost_model is not None and self._catboost_meta is not None
        rh = self._get_region_hour_df(db)
        if rh is None or rh.empty:
            return None
        region = self._resolve_region(rh, str(payload.region))
        try:
            proba, _bin = predict_region_hour_proba(
                self._catboost_model,
                self._catboost_meta,
                rh,
                region,
                hour=int(payload.hour),
            )
        except Exception:
            return None

        confidence = round(min(1.0, max(0.0, float(proba))), 2)
        method, target = self._method_target_from_incidents(payload, db)
        rationale = [
            "CatBoost region-hour model loaded from persisted artifacts: probability of a successful incident "
            f"in the following hour (region={region}, hour={payload.hour}).",
            f"Temporal risk score (probability): {confidence}.",
            f"Attack method / target object are taken from historical distribution for your org or region; "
            f"fallback: heuristic from asset type ({payload.asset_type}).",
        ]
        return MlPredictionResult(
            attack_method=method,
            target_object=target,
            confidence=confidence,
            rationale=rationale,
        )

    def predict(self, payload: PredictRequest, db: Session | None = None) -> MlPredictionResult | None:
        """Return None when data is sparse or models cannot run."""
        if self._ensure_catboost():
            out = self._predict_catboost(payload, db)
            if out is not None:
                return out

        dataset = self._build_training_dataset(db)
        if dataset.empty or len(dataset) < 10:
            return None

        org_code = str(payload.organization_id)
        org_subset = dataset[dataset["organization_code"] == org_code]
        if len(org_subset) >= 10:
            dataset = org_subset

        if len(dataset) < 10:
            return None

        bundle = self._get_or_train_sklearn_bundle(dataset)
        feature_row = {
            "organization_code": str(payload.organization_id),
            "region": payload.region,
            "industry": payload.industry,
            "season": payload.season,
            "day_of_week": payload.day_of_week,
            "hour": payload.hour,
            "has_external_access": str(payload.has_external_access),
            "privileged_accounts_count": payload.privileged_accounts_count,
            "known_vulnerabilities_count": payload.known_vulnerabilities_count,
        }
        inference_frame = pd.DataFrame([feature_row])

        method_prediction = bundle.method_pipeline.predict(inference_frame)[0]
        target_prediction = bundle.target_pipeline.predict(inference_frame)[0]

        method_confidence = max(bundle.method_pipeline.predict_proba(inference_frame)[0])
        target_confidence = max(bundle.target_pipeline.predict_proba(inference_frame)[0])
        confidence = round((float(method_confidence) + float(target_confidence)) / 2, 2)

        rationale = [
            f"ML model trained on {bundle.row_count} historical incidents from the local dataset.",
            (
                f"Primary prediction features: region {payload.region}, industry {payload.industry}, "
                f"season {payload.season}, hour {payload.hour}."
            ),
            f"Model confidence for method/target classes: {round(method_confidence, 2)}/{round(target_confidence, 2)}.",
        ]
        return MlPredictionResult(
            attack_method=str(method_prediction),
            target_object=str(target_prediction),
            confidence=confidence,
            rationale=rationale,
        )

    def _get_or_train_sklearn_bundle(self, dataset):
        """Train sklearn pipelines or reuse cached ones when the dataset size matches the cache."""
        if self._sklearn_bundle is not None and self._sklearn_bundle.row_count == len(dataset):
            return self._sklearn_bundle

        feature_columns = [
            "organization_code",
            "region",
            "industry",
            "season",
            "day_of_week",
            "hour",
            "has_external_access",
            "privileged_accounts_count",
            "known_vulnerabilities_count",
        ]
        categorical = ["organization_code", "region", "industry", "season", "has_external_access"]
        numeric = ["day_of_week", "hour", "privileged_accounts_count", "known_vulnerabilities_count"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
                ("numeric", "passthrough", numeric),
            ]
        )
        method_pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(n_estimators=200, random_state=42)),
            ]
        )
        target_pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", RandomForestClassifier(n_estimators=200, random_state=42)),
            ]
        )
        features = dataset[feature_columns]
        method_pipeline.fit(features, dataset["attack_method"])
        target_pipeline.fit(features, dataset["target_object"])
        self._sklearn_bundle = _SklearnBundle(
            method_pipeline=method_pipeline,
            target_pipeline=target_pipeline,
            row_count=len(dataset),
        )
        return self._sklearn_bundle

    def _build_training_dataset(self, db: Session | None = None):
        """Feature matrix plus attack_method/target_object labels after merging with the registry."""
        incidents = self.repository.load_incidents(db=db).copy()
        registry = self.repository.load_fstec_registry(db=db)[["threat_code", "name", "description", "object_of_impact"]]
        if incidents.empty or registry.empty:
            return incidents.iloc[0:0].copy()

        dataset = incidents.merge(registry, on="threat_code", how="left")
        dataset["attack_method"] = dataset.apply(self.analytics_service._detect_attack_method, axis=1)
        dataset["target_object"] = dataset.apply(self.analytics_service._detect_target_object, axis=1)
        dataset["has_external_access"] = dataset["target_object"].isin(["vpn_gateway", "web_portal", "mail_gateway"]).astype(str)
        dataset["privileged_accounts_count"] = (dataset["host_count"] / 20).clip(lower=1).round().astype(int)
        dataset["known_vulnerabilities_count"] = dataset["threat_code"].map(dataset["threat_code"].value_counts()).fillna(1).astype(int)
        return dataset[
            [
                "organization_code",
                "region",
                "industry",
                "season",
                "day_of_week",
                "hour",
                "has_external_access",
                "privileged_accounts_count",
                "known_vulnerabilities_count",
                "attack_method",
                "target_object",
            ]
        ].dropna()
