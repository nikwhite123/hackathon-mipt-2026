"""CatBoost training for region-risk notebook and saved backend artifacts."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from catboost import CatBoostClassifier, Pool
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

from app.ml.region_risk.features import find_best_threshold_f1, resolve_feature_columns

RANDOM_STATE = 42


@dataclass
class RegionRiskTrainingArtifacts:
    model: CatBoostClassifier
    features: list[str]
    cat_features: list[str]
    threshold: float
    cv_results: pd.DataFrame
    region_hour_df: pd.DataFrame


def _manual_param_search(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cat_features_indices: list[int],
) -> dict[str, object]:
    best_f1 = 0.0
    best_params: dict[str, object] | None = None
    param_combinations = [
        {"iterations": 400, "depth": 6, "learning_rate": 0.07, "l2_leaf_reg": 4, "bagging_temperature": 0.3},
        {"iterations": 500, "depth": 5, "learning_rate": 0.08, "l2_leaf_reg": 5, "bagging_temperature": 0.5},
        {"iterations": 600, "depth": 7, "learning_rate": 0.06, "l2_leaf_reg": 3, "bagging_temperature": 0.7},
        {"iterations": 450, "depth": 6, "learning_rate": 0.09, "l2_leaf_reg": 6, "bagging_temperature": 0.4},
    ]

    for params in param_combinations:
        model_params = {
            **params,
            "loss_function": "Logloss",
            "eval_metric": "F1",
            "auto_class_weights": "Balanced",
            "random_seed": RANDOM_STATE,
            "verbose": 0,
            "random_strength": 0.8,
        }
        model = CatBoostClassifier(**model_params)
        train_pool = Pool(X_train, y_train, cat_features=cat_features_indices)
        val_pool = Pool(X_val, y_val, cat_features=cat_features_indices)
        model.fit(
            train_pool,
            eval_set=val_pool,
            early_stopping_rounds=30,
            use_best_model=True,
            verbose=0,
        )
        val_proba = model.predict_proba(X_val)[:, 1]
        _, current_f1 = find_best_threshold_f1(y_val, val_proba)
        if current_f1 > best_f1:
            best_f1 = current_f1
            best_params = model_params

    assert best_params is not None
    return best_params


def optimize_model_with_optuna(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    cat_features_indices: list[int],
) -> dict[str, object]:
    """Optional Optuna search with manual fallback when Optuna is unavailable."""
    try:
        import optuna  # type: ignore
    except Exception:  # pragma: no cover - local environments may not have optuna
        return _manual_param_search(X_train, y_train, X_val, y_val, cat_features_indices)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "iterations": trial.suggest_int("iterations", 200, 800),
            "depth": trial.suggest_int("depth", 4, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1, 10),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0, 1),
            "random_strength": trial.suggest_float("random_strength", 0.1, 1.0),
            "loss_function": "Logloss",
            "eval_metric": "F1",
            "auto_class_weights": "Balanced",
            "random_seed": RANDOM_STATE,
            "verbose": 0,
        }
        model = CatBoostClassifier(**params)
        train_pool = Pool(X_train, y_train, cat_features=cat_features_indices)
        val_pool = Pool(X_val, y_val, cat_features=cat_features_indices)
        model.fit(
            train_pool,
            eval_set=val_pool,
            early_stopping_rounds=30,
            use_best_model=True,
            verbose=0,
        )
        val_proba = model.predict_proba(X_val)[:, 1]
        _, best_f1 = find_best_threshold_f1(y_val, val_proba)
        return best_f1

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=20)
    return {
        **study.best_params,
        "loss_function": "Logloss",
        "eval_metric": "F1",
        "auto_class_weights": "Balanced",
        "random_seed": RANDOM_STATE,
        "verbose": 0,
    }


def train_region_risk_model(
    region_hour_df: pd.DataFrame,
    *,
    use_optuna: bool = False,
    max_train_rows: int | None = None,
) -> RegionRiskTrainingArtifacts:
    """Train CatBoost exactly on the notebook feature set."""
    working = region_hour_df.sort_values(["region", "time_hour"]).reset_index(drop=True)
    if max_train_rows is not None and len(working) > max_train_rows:
        working = working.tail(max_train_rows).copy()

    feature_cols, cat_features = resolve_feature_columns(working)
    X_all = working[feature_cols]
    y_all = working["attack_present"]
    tscv = TimeSeriesSplit(n_splits=3)

    fold_results: list[dict[str, float | int]] = []
    models: list[tuple[CatBoostClassifier, list[str], list[str]]] = []
    thresholds: list[float] = []

    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_all), 1):
        X_train = X_all.iloc[train_idx].copy()
        y_train = y_all.iloc[train_idx].copy()
        X_val = X_all.iloc[val_idx].copy()
        y_val = y_all.iloc[val_idx].copy()

        cat_idx = [feature_cols.index(c) for c in cat_features if c in feature_cols]
        train_pool = Pool(X_train, y_train, cat_features=cat_idx)
        val_pool = Pool(X_val, y_val, cat_features=cat_idx)

        if use_optuna and fold <= 2 and len(y_train) > 100:
            best_params = optimize_model_with_optuna(X_train, y_train, X_val, y_val, cat_idx)
            model = CatBoostClassifier(**best_params)
        else:
            model = CatBoostClassifier(
                iterations=700,
                depth=6,
                learning_rate=0.08,
                l2_leaf_reg=5,
                bagging_temperature=0.5,
                random_strength=0.8,
                loss_function="Logloss",
                eval_metric="F1",
                auto_class_weights="Balanced",
                random_seed=RANDOM_STATE + fold,
                verbose=0,
            )

        model.fit(train_pool, eval_set=val_pool, early_stopping_rounds=50, use_best_model=True)
        val_proba = model.predict_proba(X_val)[:, 1]
        best_thr, best_f1 = find_best_threshold_f1(y_val, val_proba)
        fold_results.append(
            {
                "fold": fold,
                "f1": best_f1,
                "threshold": best_thr,
                "precision": float(precision_score(y_val, (val_proba >= best_thr).astype(int), zero_division=0)),
                "recall": float(recall_score(y_val, (val_proba >= best_thr).astype(int), zero_division=0)),
                "auc": float(roc_auc_score(y_val, val_proba)),
            }
        )
        models.append((model, feature_cols, cat_features))
        thresholds.append(best_thr)

    cv_df = pd.DataFrame(fold_results)
    best_idx = int(cv_df["f1"].idxmax())
    best_model, best_features, best_cat_features = models[best_idx]
    best_threshold = thresholds[best_idx]

    return RegionRiskTrainingArtifacts(
        model=best_model,
        features=best_features,
        cat_features=best_cat_features,
        threshold=best_threshold,
        cv_results=cv_df,
        region_hour_df=working,
    )
