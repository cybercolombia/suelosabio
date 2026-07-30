"""Construcción del dataset definitivo de rendimiento de papa."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


KEY_COLUMNS = ["codigo_municipio", "anio", "tipo_periodo", "cultivo"]
TARGET_COLUMN = "rendimiento_t_ha"
FORBIDDEN_PREDICTORS = {
    "area_cosechada_ha",
    "area_para_rendimiento_ha",
    "produccion_t",
    "produccion_para_rendimiento_t",
    "rendimiento_publicado_t_ha",
    "rendimiento_publicado_ponderado_t_ha",
}
IDENTITY_COLUMNS = [
    "codigo_municipio",
    "codigo_departamento",
    "departamento",
    "municipio",
    "anio",
    "tipo_periodo",
    "periodo",
    "cultivo",
]
HISTORY_FEATURES = [
    "rendimiento_lag_1",
    "rendimiento_lag_2",
    "rendimiento_media_historica",
    "rendimiento_std_historica",
    "rendimiento_tendencia_lag",
    "area_sembrada_lag_1",
    "area_sembrada_lag_2",
    "area_sembrada_media_historica",
    "observaciones_historia",
]
STATIC_FEATURES = [
    "latitud",
    "longitud",
    "anio_indice",
]


@dataclass(frozen=True)
class DefinitiveDatasetResult:
    dataset: pd.DataFrame
    target_municipalities: pd.DataFrame
    climate_feature_columns: tuple[str, ...]
    summary: pd.DataFrame


def _append_forecast_rows(
    potato: pd.DataFrame,
    *,
    forecast_year: int,
) -> pd.DataFrame:
    data = potato.copy()
    previous = data[data["anio"].eq(forecast_year - 1)].copy()
    if previous.empty:
        raise ValueError(f"No hay EVA {forecast_year - 1} para proyectar {forecast_year}.")
    forecast = previous.sort_values(
        ["codigo_municipio", "tipo_periodo"]
    ).drop_duplicates(["codigo_municipio", "tipo_periodo"], keep="last")
    forecast["anio"] = forecast_year
    forecast["periodo"] = str(forecast_year) + forecast["tipo_periodo"].astype(str)
    for column in (
        "area_sembrada_ha",
        "area_cosechada_ha",
        "produccion_para_rendimiento_t",
        "area_para_rendimiento_ha",
        TARGET_COLUMN,
    ):
        if column in forecast:
            forecast[column] = np.nan
    forecast["es_fila_pronostico"] = True
    data["es_fila_pronostico"] = False
    return pd.concat([data, forecast], ignore_index=True, sort=False)


def add_history_features(data: pd.DataFrame) -> pd.DataFrame:
    """Calcula rezagos con shift; ninguna fila usa su target ni el futuro."""
    result = data.sort_values(
        ["codigo_municipio", "tipo_periodo", "anio"]
    ).reset_index(drop=True)
    keys = ["codigo_municipio", "tipo_periodo"]
    yield_group = result.groupby(keys, sort=False)[TARGET_COLUMN]
    area_group = result.groupby(keys, sort=False)["area_sembrada_ha"]
    result["rendimiento_lag_1"] = yield_group.shift(1)
    result["rendimiento_lag_2"] = yield_group.shift(2)
    result["rendimiento_media_historica"] = yield_group.transform(
        lambda values: values.shift(1).expanding().mean()
    )
    result["rendimiento_std_historica"] = yield_group.transform(
        lambda values: values.shift(1).expanding().std()
    )
    result["rendimiento_tendencia_lag"] = (
        result["rendimiento_lag_1"] - result["rendimiento_lag_2"]
    )
    result["area_sembrada_lag_1"] = area_group.shift(1)
    result["area_sembrada_lag_2"] = area_group.shift(2)
    result["area_sembrada_media_historica"] = area_group.transform(
        lambda values: values.shift(1).expanding().mean()
    )
    result["observaciones_historia"] = yield_group.transform(
        lambda values: values.shift(1).expanding().count()
    )
    return result


def climate_feature_columns(indicators: pd.DataFrame) -> tuple[str, ...]:
    excluded = {
        "codigo_municipio",
        "anio",
        "tipo_periodo",
        "dias_clima_real",
        "dias_clima_climatologia",
        "tipo_escenario_climatico",
    }
    return tuple(
        column
        for column in indicators.columns
        if column not in excluded
        and pd.api.types.is_numeric_dtype(indicators[column])
    )


def build_definitive_dataset(
    potato: pd.DataFrame,
    target_municipalities: pd.DataFrame,
    municipality_cells: pd.DataFrame,
    historical_climate: pd.DataFrame,
    forecast_climate: pd.DataFrame,
    *,
    forecast_year: int = 2026,
) -> DefinitiveDatasetResult:
    """Integra EVA, historia, geografía y clima sin columnas de fuga."""
    combined = _append_forecast_rows(potato, forecast_year=forecast_year)
    combined = add_history_features(combined)
    climate_columns = climate_feature_columns(historical_climate)
    historical = historical_climate.copy()
    forecast = forecast_climate.copy()
    missing_forecast = set(climate_columns) - set(forecast.columns)
    if missing_forecast:
        raise ValueError(
            f"El escenario 2026 no tiene features climáticas: {sorted(missing_forecast)}"
        )
    climate = pd.concat(
        [
            historical[
                ["codigo_municipio", "anio", "tipo_periodo", *climate_columns]
            ],
            forecast[
                ["codigo_municipio", "anio", "tipo_periodo", *climate_columns]
            ],
        ],
        ignore_index=True,
    )
    climate = climate.sort_values(
        ["codigo_municipio", "anio", "tipo_periodo"]
    ).drop_duplicates(
        ["codigo_municipio", "anio", "tipo_periodo"], keep="last"
    )
    cells = municipality_cells[
        ["codigo_municipio", "latitud", "longitud"]
    ].copy()
    result = combined.merge(
        cells, on="codigo_municipio", how="left", validate="many_to_one"
    ).merge(
        climate,
        on=["codigo_municipio", "anio", "tipo_periodo"],
        how="left",
        validate="one_to_one",
    )
    selected_codes = set(target_municipalities["codigo_municipio"].astype(str))
    result["es_municipio_objetivo"] = (
        result["codigo_municipio"].astype(str).isin(selected_codes)
    )
    result["anio_indice"] = result["anio"].astype(int) - 2019
    result["periodo"] = (
        result["anio"].astype(int).astype(str) + result["tipo_periodo"].astype(str)
    )
    keep = [
        *IDENTITY_COLUMNS,
        "es_fila_pronostico",
        "es_municipio_objetivo",
        TARGET_COLUMN,
        *HISTORY_FEATURES,
        *STATIC_FEATURES,
        *climate_columns,
    ]
    result = result[keep].copy()
    present_forbidden = FORBIDDEN_PREDICTORS.intersection(result.columns)
    if present_forbidden:
        raise RuntimeError(
            f"El dataset definitivo conserva predictores prohibidos: "
            f"{sorted(present_forbidden)}"
        )
    if result.duplicated(KEY_COLUMNS).any():
        raise RuntimeError("El dataset definitivo contiene llaves repetidas.")
    missing_geo = result[["latitud", "longitud"]].isna().any(axis=1)
    if missing_geo.any():
        raise RuntimeError(
            f"Hay {int(missing_geo.sum())} filas sin representación geográfica."
        )
    forecast_target = result.loc[
        result["anio"].eq(forecast_year), TARGET_COLUMN
    ]
    if forecast_target.notna().any():
        raise RuntimeError("Las filas 2026 no deben contener el target.")
    summary = pd.DataFrame(
        [
            {
                "version": "papa_rendimiento_2026_v1",
                "filas": len(result),
                "filas_historicas": int(result["anio"].lt(forecast_year).sum()),
                "filas_pronostico": int(result["anio"].eq(forecast_year).sum()),
                "municipios": result["codigo_municipio"].nunique(),
                "municipios_objetivo": len(selected_codes),
                "features_historicas": len(HISTORY_FEATURES),
                "features_climaticas": len(climate_columns),
                "llaves_duplicadas": int(result.duplicated(KEY_COLUMNS).sum()),
                "predictores_prohibidos": len(present_forbidden),
            }
        ]
    )
    return DefinitiveDatasetResult(
        dataset=result.sort_values(KEY_COLUMNS).reset_index(drop=True),
        target_municipalities=target_municipalities.copy(),
        climate_feature_columns=climate_columns,
        summary=summary,
    )


def replace_test_climate(
    dataset: pd.DataFrame,
    scenario: pd.DataFrame,
    *,
    test_year: int,
    climate_columns: Iterable[str],
) -> pd.DataFrame:
    """Reemplaza solo el clima del año de prueba por su escenario as-of."""
    columns = tuple(climate_columns)
    test = dataset[dataset["anio"].eq(int(test_year))].copy()
    test = test.drop(columns=list(columns)).merge(
        scenario[
            ["codigo_municipio", "anio", "tipo_periodo", *columns]
        ],
        on=["codigo_municipio", "anio", "tipo_periodo"],
        how="left",
        validate="one_to_one",
    )
    if test[list(columns)].isna().all(axis=1).any():
        raise RuntimeError(f"Hay filas {test_year} sin escenario climático.")
    return test
