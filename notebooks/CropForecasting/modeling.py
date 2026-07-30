"""Backtesting temporal, selección de representación y pronóstico 2026."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Callable, Iterable

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .dataset import (
    HISTORY_FEATURES,
    STATIC_FEATURES,
    TARGET_COLUMN,
    replace_test_climate,
)


RANDOM_STATE = 172026
BACKTEST_YEARS = (2021, 2022, 2023, 2024, 2025)
MODEL_SELECTION_YEARS = (2024, 2025)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    encoding: str
    estimator_factory: Callable[[], object]
    scale_numeric: bool = False

    @property
    def identifier(self) -> str:
        return f"{self.name}__{self.encoding}"


@dataclass(frozen=True)
class ForecastEvaluationResult:
    leaderboard: pd.DataFrame
    fold_metrics: pd.DataFrame
    backtest_predictions: pd.DataFrame
    forecast_2026: pd.DataFrame
    selected_model: str
    selected_encoding: str
    final_estimator: object | None


class PersistenceRegressor(RegressorMixin, BaseEstimator):
    """Estimador serializable para el baseline temporal seleccionado."""

    def __init__(self, feature: str = "lag_1"):
        self.feature = feature

    def fit(self, features: pd.DataFrame, target: Iterable[float]):
        if self.feature not in {"lag_1", "media_historica"}:
            raise ValueError(f"Baseline desconocido: {self.feature}")
        values = np.asarray(list(target), dtype=float)
        self.training_median_ = float(np.nanmedian(values))
        self.n_features_in_ = len(features.columns)
        return self

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        if not hasattr(self, "training_median_"):
            raise RuntimeError("PersistenceRegressor debe entrenarse antes de predecir.")
        if self.feature == "lag_1":
            values = features["rendimiento_lag_1"]
        else:
            values = features["rendimiento_media_historica"]
        fallback = features["rendimiento_media_historica"].fillna(
            features["rendimiento_lag_1"]
        )
        return (
            values.fillna(fallback)
            .fillna(self.training_median_)
            .astype(float)
            .to_numpy()
        )


def regression_metrics(
    observed: Iterable[float], predicted: Iterable[float]
) -> dict[str, float]:
    actual = np.asarray(list(observed), dtype=float)
    estimate = np.asarray(list(predicted), dtype=float)
    valid = np.isfinite(actual) & np.isfinite(estimate)
    actual, estimate = actual[valid], estimate[valid]
    if len(actual) == 0:
        return {
            "n": 0,
            "mae": np.nan,
            "rmse": np.nan,
            "r2": np.nan,
            "mape_pct": np.nan,
            "smape_pct": np.nan,
        }
    nonzero = np.abs(actual) > 1e-12
    mape = (
        100 * np.mean(np.abs((actual[nonzero] - estimate[nonzero]) / actual[nonzero]))
        if nonzero.any()
        else np.nan
    )
    denominator = np.abs(actual) + np.abs(estimate)
    smape_valid = denominator > 1e-12
    smape = (
        200
        * np.mean(
            np.abs(actual[smape_valid] - estimate[smape_valid])
            / denominator[smape_valid]
        )
        if smape_valid.any()
        else np.nan
    )
    return {
        "n": int(len(actual)),
        "mae": float(mean_absolute_error(actual, estimate)),
        "rmse": float(math.sqrt(mean_squared_error(actual, estimate))),
        "r2": float(r2_score(actual, estimate)) if len(actual) >= 2 else np.nan,
        "mape_pct": float(mape),
        "smape_pct": float(smape),
    }


def default_model_specs() -> tuple[ModelSpec, ...]:
    """Incluye ML lineal, ensambles, boosting y una red pequeña."""
    specs = [
        ModelSpec(
            "ridge",
            "one_hot_entity",
            lambda: Ridge(alpha=10.0),
            scale_numeric=True,
        ),
        ModelSpec(
            "ridge",
            "geo_history",
            lambda: Ridge(alpha=10.0),
            scale_numeric=True,
        ),
        ModelSpec(
            "extra_trees",
            "one_hot_entity",
            lambda: ExtraTreesRegressor(
                n_estimators=500,
                min_samples_leaf=2,
                max_features=0.8,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
        ModelSpec(
            "extra_trees",
            "geo_history",
            lambda: ExtraTreesRegressor(
                n_estimators=500,
                min_samples_leaf=2,
                max_features=0.8,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
        ModelSpec(
            "random_forest",
            "geo_history",
            lambda: RandomForestRegressor(
                n_estimators=500,
                min_samples_leaf=3,
                max_features=0.75,
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
        ModelSpec(
            "hist_gradient_boosting",
            "geo_history",
            lambda: HistGradientBoostingRegressor(
                learning_rate=0.05,
                max_iter=300,
                max_leaf_nodes=15,
                l2_regularization=1.0,
                random_state=RANDOM_STATE,
            ),
        ),
        ModelSpec(
            "mlp",
            "geo_history",
            lambda: MLPRegressor(
                hidden_layer_sizes=(48, 24),
                alpha=0.05,
                learning_rate_init=0.001,
                max_iter=800,
                early_stopping=True,
                random_state=RANDOM_STATE,
            ),
            scale_numeric=True,
        ),
    ]
    try:
        from xgboost import XGBRegressor
    except Exception:
        # En macOS XGBoost puede requerir libomp; el resto del benchmark no
        # debe bloquearse por una dependencia opcional.
        return tuple(specs)
    for encoding in ("one_hot_entity", "geo_history"):
        specs.append(
            ModelSpec(
                "xgboost",
                encoding,
                lambda: XGBRegressor(
                    objective="reg:squarederror",
                    n_estimators=400,
                    learning_rate=0.03,
                    max_depth=3,
                    min_child_weight=3,
                    subsample=0.85,
                    colsample_bytree=0.85,
                    reg_lambda=3.0,
                    random_state=RANDOM_STATE,
                    n_jobs=2,
                ),
            )
        )
    return tuple(specs)


def _feature_groups(
    climate_columns: Iterable[str],
    encoding: str,
) -> tuple[list[str], list[str]]:
    numeric = [*HISTORY_FEATURES, *STATIC_FEATURES, *climate_columns]
    if encoding == "one_hot_entity":
        categorical = [
            "codigo_municipio",
            "codigo_departamento",
            "tipo_periodo",
        ]
    elif encoding == "geo_history":
        categorical = ["codigo_departamento", "tipo_periodo"]
    else:
        raise ValueError(f"Representación desconocida: {encoding}")
    return numeric, categorical


def _pipeline(spec: ModelSpec, climate_columns: Iterable[str]) -> Pipeline:
    numeric, categorical = _feature_groups(climate_columns, spec.encoding)
    numeric_steps: list[tuple[str, object]] = [
        (
            "imputer",
            SimpleImputer(
                strategy="median",
                add_indicator=True,
                keep_empty_features=True,
            ),
        )
    ]
    if spec.scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    preprocessor = ColumnTransformer(
        [
            ("numeric", Pipeline(numeric_steps), numeric),
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="most_frequent",
                                keep_empty_features=True,
                            ),
                        ),
                        (
                            "one_hot",
                            OneHotEncoder(
                                handle_unknown="ignore", sparse_output=False
                            ),
                        ),
                    ]
                ),
                categorical,
            ),
        ],
        remainder="drop",
    )
    return Pipeline(
        [("features", preprocessor), ("model", spec.estimator_factory())]
    )


def _baseline_prediction(test: pd.DataFrame, baseline: str) -> np.ndarray:
    if baseline == "lag_1":
        values = test["rendimiento_lag_1"]
    elif baseline == "media_historica":
        values = test["rendimiento_media_historica"]
    else:
        raise ValueError(f"Baseline desconocido: {baseline}")
    fallback = test["rendimiento_media_historica"].fillna(
        test["rendimiento_lag_1"]
    )
    return values.fillna(fallback).astype(float).to_numpy()


def _scenario_for_year(scenarios: pd.DataFrame, year: int) -> pd.DataFrame:
    selected = scenarios[scenarios["anio"].eq(int(year))].copy()
    if selected.empty:
        raise ValueError(f"No existe escenario climático as-of para {year}.")
    return selected


def run_temporal_backtesting(
    dataset: pd.DataFrame,
    scenarios: pd.DataFrame,
    climate_columns: Iterable[str],
    *,
    backtest_years: Iterable[int] = BACKTEST_YEARS,
    selection_years: Iterable[int] = MODEL_SELECTION_YEARS,
    model_specs: Iterable[ModelSpec] | None = None,
    forecast_year: int = 2026,
) -> ForecastEvaluationResult:
    """Selecciona por años recientes y genera el pronóstico final 2026."""
    climate_columns = tuple(climate_columns)
    specs = tuple(model_specs or default_model_specs())
    fold_metric_rows: list[dict] = []
    prediction_frames: list[pd.DataFrame] = []

    for test_year in tuple(int(year) for year in backtest_years):
        train = dataset[
            dataset["anio"].lt(test_year)
            & dataset[TARGET_COLUMN].notna()
            & ~dataset["es_fila_pronostico"]
        ].copy()
        test = replace_test_climate(
            dataset,
            _scenario_for_year(scenarios, test_year),
            test_year=test_year,
            climate_columns=climate_columns,
        )
        test = test[
            test["es_municipio_objetivo"] & test[TARGET_COLUMN].notna()
        ].copy()
        if train.empty or test.empty:
            raise RuntimeError(f"Fold temporal {test_year} sin train o test.")
        for baseline in ("lag_1", "media_historica"):
            predicted = _baseline_prediction(test, baseline)
            metrics = regression_metrics(test[TARGET_COLUMN], predicted)
            identifier = f"baseline_{baseline}"
            fold_metric_rows.append(
                {
                    "candidate": identifier,
                    "model": "baseline",
                    "encoding": baseline,
                    "test_year": test_year,
                    **metrics,
                }
            )
            frame = test[
                [
                    "codigo_municipio",
                    "departamento",
                    "municipio",
                    "anio",
                    "tipo_periodo",
                    TARGET_COLUMN,
                ]
            ].copy()
            frame["candidate"] = identifier
            frame["prediccion_t_ha"] = predicted
            prediction_frames.append(frame)
        for spec in specs:
            estimator = _pipeline(spec, climate_columns)
            estimator.fit(train, train[TARGET_COLUMN].astype(float))
            predicted = estimator.predict(test)
            metrics = regression_metrics(test[TARGET_COLUMN], predicted)
            fold_metric_rows.append(
                {
                    "candidate": spec.identifier,
                    "model": spec.name,
                    "encoding": spec.encoding,
                    "test_year": test_year,
                    **metrics,
                }
            )
            frame = test[
                [
                    "codigo_municipio",
                    "departamento",
                    "municipio",
                    "anio",
                    "tipo_periodo",
                    TARGET_COLUMN,
                ]
            ].copy()
            frame["candidate"] = spec.identifier
            frame["prediccion_t_ha"] = predicted
            prediction_frames.append(frame)

    fold_metrics = pd.DataFrame(fold_metric_rows)
    selection_years_set = {int(year) for year in selection_years}
    leaderboard = (
        fold_metrics[fold_metrics["test_year"].isin(selection_years_set)]
        .groupby(["candidate", "model", "encoding"], as_index=False)
        .agg(
            folds=("test_year", "nunique"),
            observaciones=("n", "sum"),
            mae_media=("mae", "mean"),
            rmse_media=("rmse", "mean"),
            r2_media=("r2", "mean"),
            smape_media_pct=("smape_pct", "mean"),
        )
        .sort_values(["mae_media", "rmse_media", "candidate"])
        .reset_index(drop=True)
    )
    leaderboard["ranking_mae_2024_2025"] = np.arange(1, len(leaderboard) + 1)
    winner = leaderboard.iloc[0]
    selected_candidate = str(winner["candidate"])
    selected_model = str(winner["model"])
    selected_encoding = str(winner["encoding"])

    predictions = pd.concat(prediction_frames, ignore_index=True)
    selected_backtests = predictions[
        predictions["candidate"].eq(selected_candidate)
    ].copy()
    residual_quantile = float(
        np.quantile(
            np.abs(
                selected_backtests[TARGET_COLUMN]
                - selected_backtests["prediccion_t_ha"]
            ),
            0.9,
        )
    )
    forecast = dataset[
        dataset["anio"].eq(forecast_year) & dataset["es_municipio_objetivo"]
    ].copy()
    if len(forecast) != 40:
        raise RuntimeError(
            f"Se esperaban 40 filas objetivo 2026 y se obtuvieron {len(forecast)}."
        )
    final_train = dataset[
        dataset["anio"].lt(forecast_year)
        & dataset[TARGET_COLUMN].notna()
        & ~dataset["es_fila_pronostico"]
    ].copy()
    final_estimator: object | None
    if selected_model == "baseline":
        final_estimator = PersistenceRegressor(selected_encoding).fit(
            final_train, final_train[TARGET_COLUMN]
        )
        forecast_prediction = final_estimator.predict(forecast)
    else:
        selected_spec = next(
            spec for spec in specs if spec.identifier == selected_candidate
        )
        final_estimator = _pipeline(selected_spec, climate_columns)
        final_estimator.fit(final_train, final_train[TARGET_COLUMN].astype(float))
        forecast_prediction = final_estimator.predict(forecast)
    output = forecast[
        [
            "codigo_municipio",
            "codigo_departamento",
            "departamento",
            "municipio",
            "anio",
            "tipo_periodo",
            "periodo",
            "rendimiento_lag_1",
            "rendimiento_media_historica",
        ]
    ].copy()
    output["modelo"] = selected_model
    output["representacion"] = selected_encoding
    output["prediccion_rendimiento_t_ha"] = np.maximum(
        np.asarray(forecast_prediction, dtype=float), 0
    )
    output["intervalo_p10_t_ha"] = np.maximum(
        output["prediccion_rendimiento_t_ha"] - residual_quantile, 0
    )
    output["intervalo_p90_t_ha"] = (
        output["prediccion_rendimiento_t_ha"] + residual_quantile
    )
    output["intervalo_metodo"] = "RESIDUO_ABSOLUTO_P90_BACKTEST_2021_2025"
    return ForecastEvaluationResult(
        leaderboard=leaderboard,
        fold_metrics=fold_metrics.sort_values(
            ["test_year", "mae", "candidate"]
        ).reset_index(drop=True),
        backtest_predictions=selected_backtests.sort_values(
            ["anio", "departamento", "municipio", "tipo_periodo"]
        ).reset_index(drop=True),
        forecast_2026=output.sort_values(
            ["departamento", "tipo_periodo", "municipio"]
        ).reset_index(drop=True),
        selected_model=selected_model,
        selected_encoding=selected_encoding,
        final_estimator=final_estimator,
    )


def metric_breakdown(predictions: pd.DataFrame) -> pd.DataFrame:
    """Métricas del ganador por año, departamento y semestre."""
    rows: list[dict] = []
    groupings = {
        "GLOBAL": [],
        "ANIO": ["anio"],
        "DEPARTAMENTO": ["departamento"],
        "SEMESTRE": ["tipo_periodo"],
        "DEPARTAMENTO_SEMESTRE": ["departamento", "tipo_periodo"],
    }
    for level, columns in groupings.items():
        groups = (
            [((), predictions)]
            if not columns
            else predictions.groupby(columns, dropna=False)
        )
        for key, group in groups:
            key_values = key if isinstance(key, tuple) else (key,)
            identity = dict(zip(columns, key_values))
            rows.append(
                {
                    "nivel": level,
                    **identity,
                    **regression_metrics(
                        group[TARGET_COLUMN], group["prediccion_t_ha"]
                    ),
                }
            )
    return pd.DataFrame(rows)
