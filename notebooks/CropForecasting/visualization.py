"""Gráficas históricas y de pronóstico para todos los features evaluados."""

from __future__ import annotations

from collections.abc import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .dataset import HISTORY_FEATURES, STATIC_FEATURES


EMBEDDING_COLUMNS = {
    "one_hot_entity": (
        "codigo_municipio",
        "codigo_departamento",
        "tipo_periodo",
    ),
    "geo_history": ("codigo_departamento", "tipo_periodo"),
}


def model_feature_inventory(
    climate_columns: Iterable[str],
) -> pd.DataFrame:
    rows = []
    for column in HISTORY_FEATURES:
        rows.append(
            {"variable": column, "grupo": "HISTORIA", "tipo": "NUMERICA"}
        )
    for column in STATIC_FEATURES:
        rows.append(
            {"variable": column, "grupo": "GEOGRAFIA_TIEMPO", "tipo": "NUMERICA"}
        )
    for column in climate_columns:
        rows.append(
            {"variable": column, "grupo": "CLIMA", "tipo": "NUMERICA"}
        )
    for encoding, columns in EMBEDDING_COLUMNS.items():
        for column in columns:
            rows.append(
                {
                    "variable": column,
                    "grupo": encoding,
                    "tipo": "CATEGORICA_CODIFICADA",
                }
            )
    return pd.DataFrame(rows).drop_duplicates().reset_index(drop=True)


def plot_numeric_feature_history(
    dataset: pd.DataFrame,
    feature: str,
) -> plt.Figure:
    """Una figura por feature, con mediana y rango intercuartílico por semestre."""
    if feature not in dataset:
        raise KeyError(f"El dataset no contiene {feature}.")
    data = dataset[
        dataset["anio"].le(2025) & dataset["rendimiento_t_ha"].notna()
    ].copy()
    data[feature] = pd.to_numeric(data[feature], errors="coerce")
    summary = (
        data.groupby(["anio", "tipo_periodo"])[feature]
        .agg(
            mediana="median",
            q25=lambda values: values.quantile(0.25),
            q75=lambda values: values.quantile(0.75),
            observaciones="count",
        )
        .reset_index()
    )
    figure, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
    for axis, period in zip(axes, ("A", "B")):
        selected = summary[summary["tipo_periodo"].eq(period)]
        axis.plot(
            selected["anio"],
            selected["mediana"],
            marker="o",
            linewidth=2,
            color="#2f6f4e",
        )
        axis.fill_between(
            selected["anio"],
            selected["q25"].astype(float),
            selected["q75"].astype(float),
            color="#8fc4a8",
            alpha=0.35,
            label="Q25–Q75",
        )
        axis.set_title(f"Semestre {period}")
        axis.set_xlabel("Año")
        axis.grid(alpha=0.2)
    axes[0].set_ylabel(feature)
    figure.suptitle(f"Comportamiento histórico: {feature}")
    figure.tight_layout()
    return figure


def plot_categorical_encoding(
    dataset: pd.DataFrame,
    column: str,
    *,
    top_n: int = 20,
) -> plt.Figure:
    """Grafica frecuencia histórica de cada variable categórica codificada."""
    if column not in dataset:
        raise KeyError(f"El dataset no contiene {column}.")
    data = dataset[
        dataset["anio"].le(2025) & dataset["rendimiento_t_ha"].notna()
    ]
    counts = data[column].astype("string").value_counts().head(top_n).sort_values()
    figure, axis = plt.subplots(figsize=(10, max(4, 0.3 * len(counts))))
    counts.plot.barh(ax=axis, color="#527da3")
    axis.set_title(f"Frecuencia histórica de la categoría: {column}")
    axis.set_xlabel("Filas municipio-semestre")
    axis.grid(axis="x", alpha=0.2)
    figure.tight_layout()
    return figure


def plot_forecast_panels(forecast: pd.DataFrame) -> plt.Figure:
    """Cuatro paneles: departamento por semestre, con intervalo empírico."""
    figure, axes = plt.subplots(2, 2, figsize=(15, 13))
    departments = ("Boyacá", "Cundinamarca")
    periods = ("A", "B")
    for row, department in enumerate(departments):
        for column, period in enumerate(periods):
            axis = axes[row, column]
            selected = forecast[
                forecast["departamento"].eq(department)
                & forecast["tipo_periodo"].eq(period)
            ].sort_values("prediccion_rendimiento_t_ha")
            center = selected["prediccion_rendimiento_t_ha"].to_numpy()
            lower = center - selected["intervalo_p10_t_ha"].to_numpy()
            upper = selected["intervalo_p90_t_ha"].to_numpy() - center
            positions = np.arange(len(selected))
            axis.errorbar(
                center,
                positions,
                xerr=np.vstack([lower, upper]),
                fmt="o",
                color="#8f4f31",
                ecolor="#d19b7d",
                capsize=3,
            )
            axis.set_yticks(positions, selected["municipio"])
            axis.set_title(f"{department} — 2026{period}")
            axis.set_xlabel("Rendimiento pronosticado (t/ha)")
            axis.grid(axis="x", alpha=0.2)
    figure.suptitle("Pronóstico de rendimiento de papa 2026")
    figure.tight_layout()
    return figure
