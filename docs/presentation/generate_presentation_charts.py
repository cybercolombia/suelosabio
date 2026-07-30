"""Genera las figuras reproducibles del resumen técnico del proyecto.

Las figuras se construyen exclusivamente desde los artefactos versionados del
pipeline. El script no modifica los datasets de Google Drive.
"""

from __future__ import annotations

import os
from pathlib import Path
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize
from matplotlib.patches import Patch
import geopandas as gpd
import numpy as np
import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = Path(__file__).resolve().parent / "assets"
DEFAULT_PROCESSED_ROOT = Path(
    "/Users/eshernan/Library/CloudStorage/"
    "GoogleDrive-eshernan@gmail.com/.shortcut-targets-by-id/"
    "1aKoa_whG2LeZ05qCPObUHWR0-xZ95Qn7/eco2026_processed"
)
PROCESSED_ROOT = Path(
    os.environ.get("ECO2026_PROCESSED_ROOT", DEFAULT_PROCESSED_ROOT)
)
DEFAULT_SHARED_ROOT = Path(
    "/Users/eshernan/Library/CloudStorage/"
    "GoogleDrive-eshernan@gmail.com/My Drive/eco2026"
)
SHARED_ROOT = Path(
    os.environ.get("ECO2026_SHARED_ROOT", DEFAULT_SHARED_ROOT)
)
MUNICIPAL_GEOPACKAGE = SHARED_ROOT / "Boyaca_Cundinamarca_Municipios.gpkg"

CLIMATE_VARIABLES = {
    "precipitacion": {
        "label": "Precipitación",
        "unit": "mm",
        "column": "precipitacion_municipal_mm",
        "monthly": "sum",
    },
    "temperatura_ambiente": {
        "label": "Temperatura ambiente",
        "unit": "°C",
        "column": "valor_municipal",
        "monthly": "mean",
    },
    "temperatura_minima": {
        "label": "Temperatura mínima",
        "unit": "°C",
        "column": "valor_municipal",
        "monthly": "mean",
    },
    "temperatura_maxima": {
        "label": "Temperatura máxima",
        "unit": "°C",
        "column": "valor_municipal",
        "monthly": "mean",
    },
    "velocidad_viento": {
        "label": "Velocidad del viento",
        "unit": "m/s",
        "column": "valor_municipal",
        "monthly": "mean",
    },
    "presion_atmosferica": {
        "label": "Presión atmosférica",
        "unit": "hPa",
        "column": "valor_municipal",
        "monthly": "mean",
    },
}

DEPARTMENT_COLORS = {
    "Boyacá": "#2166ac",
    "Cundinamarca": "#b2182b",
}

CROP_COLORS = [
    "#1b9e77",
    "#d95f02",
    "#7570b3",
    "#e7298a",
    "#66a61e",
    "#e6ab02",
    "#a6761d",
    "#1f78b4",
    "#b2df8a",
    "#fb9a99",
]


def _plain(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in text if not unicodedata.combining(char))


def _department_name(value: object) -> str:
    plain = _plain(value).strip().casefold()
    if plain == "boyaca":
        return "Boyacá"
    if plain == "cundinamarca":
        return "Cundinamarca"
    return str(value)


def _municipal_files(variable: str) -> list[Path]:
    root = PROCESSED_ROOT / "clima_municipal" / f"variable={variable}"
    files = sorted(root.glob("fuente=*/agregacion=*/departamento=*/anio=*/mes=*/*.parquet"))
    if not files:
        raise FileNotFoundError(f"No se hallaron particiones municipales para {variable}")
    return files


def load_station_climate() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for variable, metadata in CLIMATE_VARIABLES.items():
        for path in _municipal_files(variable):
            data = pd.read_parquet(
                path,
                columns=[
                    "departamento",
                    "fecha",
                    metadata["column"],
                    "es_valido_municipio_dia",
                ],
            )
            data = data.rename(columns={metadata["column"]: "valor"})
            data["departamento"] = data["departamento"].map(_department_name)
            data["fecha"] = pd.to_datetime(data["fecha"])
            data["valor"] = pd.to_numeric(data["valor"], errors="coerce")
            data["valor_valido"] = data["valor"].where(
                data["es_valido_municipio_dia"]
            )
            summary = (
                data.groupby(["departamento", "fecha"], as_index=False)
                .agg(
                    valor=("valor_valido", "median"),
                    municipios_validos=("es_valido_municipio_dia", "sum"),
                    municipios_total=("es_valido_municipio_dia", "size"),
                )
            )
            summary["variable"] = variable
            frames.append(summary)
    result = pd.concat(frames, ignore_index=True)
    result["cobertura_pct"] = (
        result["municipios_validos"] / result["municipios_total"] * 100
    )
    return result


def _save(figure: plt.Figure, filename: str) -> None:
    figure.savefig(
        OUTPUT_ROOT / filename,
        dpi=180,
        bbox_inches="tight",
        facecolor="white",
    )
    plt.close(figure)


def load_municipal_geography() -> gpd.GeoDataFrame:
    if not MUNICIPAL_GEOPACKAGE.exists():
        raise FileNotFoundError(
            "No existe el GeoPackage municipal. Defina ECO2026_SHARED_ROOT con "
            "la carpeta que contiene Boyaca_Cundinamarca_Municipios.gpkg."
        )
    municipalities = gpd.read_file(MUNICIPAL_GEOPACKAGE)
    municipalities["codigo_municipio"] = (
        municipalities["DPTO_CCDGO"].astype("string").str.zfill(2)
        + municipalities["MPIO_CCDGO"].astype("string").str.zfill(3)
    )
    municipalities["departamento"] = (
        municipalities["DEPTO"].map(_department_name)
    )
    municipalities["municipio"] = municipalities["MPIO_CNMBR"].str.title()
    return municipalities[
        ["codigo_municipio", "departamento", "municipio", "geometry"]
    ].to_crs(9377)


def _base_map(
    axis: plt.Axes,
    municipalities: gpd.GeoDataFrame,
    *,
    department: str | None = None,
) -> gpd.GeoDataFrame:
    selected = (
        municipalities[municipalities["departamento"].eq(department)]
        if department
        else municipalities
    )
    selected.plot(
        ax=axis,
        color="#f2f2f2",
        edgecolor="#bdbdbd",
        linewidth=0.35,
    )
    selected.dissolve(by="departamento").boundary.plot(
        ax=axis,
        color="#525252",
        linewidth=0.9,
    )
    axis.set_axis_off()
    axis.set_aspect("equal")
    return selected


def _add_numeric_colorbar(
    figure: plt.Figure,
    axis: plt.Axes,
    *,
    cmap: str,
    norm: Normalize,
    label: str,
) -> None:
    scalar = matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar.set_array([])
    colorbar = figure.colorbar(scalar, ax=axis, fraction=0.035, pad=0.015)
    colorbar.set_label(label)


def _plot_numeric_layer(
    figure: plt.Figure,
    axis: plt.Axes,
    frame: gpd.GeoDataFrame,
    *,
    column: str,
    title: str,
    colorbar_label: str,
    cmap: str = "YlOrRd",
    logarithmic: bool = False,
    norm: Normalize | None = None,
) -> Normalize:
    values = pd.to_numeric(frame[column], errors="coerce")
    positive = values[values.gt(0)]
    if norm is None:
        if logarithmic and not positive.empty:
            norm = LogNorm(vmin=float(positive.min()), vmax=float(positive.max()))
        else:
            valid = values.dropna()
            norm = Normalize(
                vmin=float(valid.min()) if not valid.empty else 0,
                vmax=float(valid.max()) if not valid.empty else 1,
            )
    frame.plot(
        ax=axis,
        column=column,
        cmap=cmap,
        norm=norm,
        edgecolor="#bdbdbd",
        linewidth=0.35,
        missing_kwds={"color": "#f2f2f2"},
    )
    frame.dissolve(by="departamento").boundary.plot(
        ax=axis,
        color="#525252",
        linewidth=0.9,
    )
    axis.set_title(title)
    axis.set_axis_off()
    axis.set_aspect("equal")
    _add_numeric_colorbar(
        figure,
        axis,
        cmap=cmap,
        norm=norm,
        label=colorbar_label,
    )
    return norm


def plot_one_month(climate: pd.DataFrame) -> None:
    daily = climate[
        climate["fecha"].between("2025-01-01", "2025-01-31")
    ].copy()
    figure, axes = plt.subplots(3, 2, figsize=(14, 11), sharex=True)
    for axis, (variable, metadata) in zip(axes.flat, CLIMATE_VARIABLES.items()):
        selected = daily[daily["variable"].eq(variable)]
        for department, color in DEPARTMENT_COLORS.items():
            series = selected[selected["departamento"].eq(department)]
            if variable == "precipitacion":
                axis.step(
                    series["fecha"],
                    series["valor"],
                    where="mid",
                    linewidth=1.6,
                    color=color,
                    label=department,
                )
            else:
                axis.plot(
                    series["fecha"],
                    series["valor"],
                    linewidth=1.7,
                    color=color,
                    label=department,
                )
        axis.set_title(metadata["label"])
        axis.set_ylabel(metadata["unit"])
        axis.grid(alpha=0.22)
    axes[0, 0].legend(frameon=False, ncol=2)
    for axis in axes[-1, :]:
        axis.set_xlabel("Día de enero de 2025")
    figure.suptitle(
        "Clima municipal en enero de 2025: mediana diaria de municipios con dato válido",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "01_clima_un_mes.png")


def plot_several_months(climate: pd.DataFrame) -> None:
    regional_daily = climate.copy()
    regional_daily["mes"] = regional_daily["fecha"].dt.to_period("M").dt.to_timestamp()
    frames: list[pd.DataFrame] = []
    for variable, metadata in CLIMATE_VARIABLES.items():
        selected = regional_daily[regional_daily["variable"].eq(variable)]
        operation = metadata["monthly"]
        monthly = (
            selected.groupby(["variable", "departamento", "mes"], as_index=False)[
                "valor"
            ]
            .agg(operation)
        )
        frames.append(monthly)
    summary = pd.concat(frames, ignore_index=True)

    figure, axes = plt.subplots(3, 2, figsize=(14, 11), sharex=True)
    for axis, (variable, metadata) in zip(axes.flat, CLIMATE_VARIABLES.items()):
        selected = summary[summary["variable"].eq(variable)]
        for department, color in DEPARTMENT_COLORS.items():
            series = selected[selected["departamento"].eq(department)]
            axis.plot(
                series["mes"],
                series["valor"],
                marker="o",
                markersize=3,
                linewidth=1.6,
                color=color,
                label=department,
            )
        suffix = "acumulada" if variable == "precipitacion" else "promedio"
        axis.set_title(f"{metadata['label']} mensual {suffix}")
        axis.set_ylabel(metadata["unit"])
        axis.grid(alpha=0.22)
    axes[0, 0].legend(frameon=False, ncol=2)
    for axis in axes[-1, :]:
        axis.set_xlabel("Mes")
    figure.suptitle(
        "Variación mensual 2024–2025 a partir de la capa municipio-día",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "02_clima_varios_meses.png")


def plot_february_gap(climate: pd.DataFrame) -> None:
    february = climate[climate["fecha"].between("2025-02-01", "2025-02-28")].copy()
    coverage = (
        february.groupby(["variable", "fecha"])
        .agg(
            municipios_validos=("municipios_validos", "sum"),
            municipios_total=("municipios_total", "sum"),
        )
        .assign(
            cobertura_pct=lambda frame: (
                frame["municipios_validos"] / frame["municipios_total"] * 100
            )
        )["cobertura_pct"]
        .unstack("fecha")
    )
    coverage = coverage.reindex(CLIMATE_VARIABLES)
    coverage.columns = [date.day for date in coverage.columns]
    coverage = coverage.astype(float)
    colors = LinearSegmentedColormap.from_list(
        "coverage",
        ["#b2182b", "#f7f7f7", "#2166ac"],
    )
    figure, axis = plt.subplots(figsize=(14, 5))
    image = axis.imshow(
        coverage.to_numpy(),
        aspect="auto",
        vmin=0,
        vmax=max(1, float(np.nanmax(coverage.to_numpy()))),
        cmap=colors,
    )
    axis.set_yticks(
        np.arange(len(coverage)),
        [CLIMATE_VARIABLES[item]["label"] for item in coverage.index],
    )
    axis.set_xticks(np.arange(len(coverage.columns)), coverage.columns)
    axis.set_xlabel("Día de febrero de 2025")
    axis.set_title(
        "Cobertura municipal diaria por variable, febrero de 2025"
    )
    colorbar = figure.colorbar(image, ax=axis, pad=0.02)
    colorbar.set_label("Municipios con dato válido (%)")
    figure.tight_layout()
    _save(figure, "03_brecha_febrero_2025.png")


def load_agriculture() -> pd.DataFrame:
    path = (
        PROCESSED_ROOT
        / "agricultura_municipal"
        / "version=cultivo_municipio_periodo_v1"
        / "cultivo_municipio_periodo.parquet"
    )
    return pd.read_parquet(path)


def plot_crop_periods(agriculture: pd.DataFrame) -> None:
    counts = (
        agriculture.groupby(["anio", "tipo_periodo"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["A", "B", "ANUAL"], fill_value=0)
    )
    figure, axis = plt.subplots(figsize=(10, 5.5))
    counts.plot(
        kind="bar",
        stacked=True,
        ax=axis,
        color=["#2166ac", "#67a9cf", "#bdbdbd"],
        width=0.68,
    )
    axis.set_title("Registros agrícolas por tipo de período")
    axis.set_xlabel("Año")
    axis.set_ylabel("Filas municipio × cultivo × período")
    axis.legend(title="Tipo de período", frameon=False, ncol=3)
    axis.grid(axis="y", alpha=0.22)
    axis.tick_params(axis="x", rotation=0)
    figure.tight_layout()
    _save(figure, "04_agricultura_periodos.png")


def plot_crop_selection(agriculture: pd.DataFrame) -> None:
    semester = agriculture[agriculture["tipo_periodo"].isin(["A", "B"])].copy()
    ranking = (
        semester.groupby("cultivo", as_index=False)
        .agg(area_sembrada_ha=("area_sembrada_ha", "sum"))
        .sort_values("area_sembrada_ha", ascending=False)
        .head(10)
        .sort_values("area_sembrada_ha")
    )
    colors = [
        "#b2182b" if crop == "Papa" else "#92c5de" for crop in ranking["cultivo"]
    ]
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(ranking["cultivo"], ranking["area_sembrada_ha"], color=colors)
    axis.set_title("Cultivos transitorios con mayor área sembrada acumulada")
    axis.set_xlabel("Área sembrada en períodos A y B, 2022–2024 (hectáreas)")
    axis.grid(axis="x", alpha=0.22)
    for position, value in enumerate(ranking["area_sembrada_ha"]):
        axis.text(
            value,
            position,
            f" {value:,.0f}".replace(",", "."),
            va="center",
            fontsize=8,
        )
    figure.tight_layout()
    _save(figure, "05_seleccion_cultivo_papa.png")


def load_climate_stations() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for variable in CLIMATE_VARIABLES:
        path = (
            PROCESSED_ROOT
            / "geografia_curada"
            / f"canonica=estaciones_{variable}_2024_2025_v3"
            / "estaciones_municipio.parquet"
        )
        data = pd.read_parquet(
            path,
            columns=[
                "codigoestacion",
                "LATITUD",
                "LONGITUD",
                "estado_asignacion",
            ],
        )
        data["variable"] = variable
        frames.append(data)
    stations = pd.concat(frames, ignore_index=True)
    stations = stations[
        stations["estado_asignacion"].eq("ASIGNACION_CANONICA")
        & stations["LATITUD"].notna()
        & stations["LONGITUD"].notna()
    ].copy()
    return (
        stations.groupby("codigoestacion", as_index=False)
        .agg(
            latitud=("LATITUD", "median"),
            longitud=("LONGITUD", "median"),
            variables=("variable", "nunique"),
        )
    )


def plot_station_locations(
    municipalities: gpd.GeoDataFrame,
    stations: pd.DataFrame,
) -> None:
    points = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations["longitud"], stations["latitud"]),
        crs=4326,
    ).to_crs(municipalities.crs)
    figure, axis = plt.subplots(figsize=(10, 10))
    _base_map(axis, municipalities)
    norm = Normalize(vmin=1, vmax=len(CLIMATE_VARIABLES))
    points.plot(
        ax=axis,
        column="variables",
        cmap="viridis",
        norm=norm,
        markersize=14 + points["variables"] * 9,
        edgecolor="white",
        linewidth=0.35,
        alpha=0.9,
        zorder=3,
    )
    _add_numeric_colorbar(
        figure,
        axis,
        cmap="viridis",
        norm=norm,
        label="Variables climáticas con asignación canónica",
    )
    axis.set_title(
        f"Estaciones con asignación municipal canónica, 2024–2025 ({len(points)})"
    )
    figure.tight_layout()
    _save(figure, "10_mapa_estaciones_climaticas.png")


def _top_crops(agriculture: pd.DataFrame, count: int = 10) -> pd.Series:
    valid = agriculture[agriculture["area_sembrada_ha"].gt(0)]
    return (
        valid.groupby("cultivo")["area_sembrada_ha"]
        .sum()
        .sort_values(ascending=False)
        .head(count)
    )


def plot_dominant_crops(
    municipalities: gpd.GeoDataFrame,
    agriculture: pd.DataFrame,
) -> None:
    ranking = _top_crops(agriculture)
    selected = agriculture[agriculture["cultivo"].isin(ranking.index)].copy()
    by_municipality = (
        selected.groupby(["codigo_municipio", "cultivo"], as_index=False)[
            "area_sembrada_ha"
        ]
        .sum()
        .sort_values(
            ["codigo_municipio", "area_sembrada_ha"],
            ascending=[True, False],
        )
        .drop_duplicates("codigo_municipio")
    )
    mapped = municipalities.merge(by_municipality, on="codigo_municipio", how="left")
    color_by_crop = {
        crop: CROP_COLORS[position]
        for position, crop in enumerate(ranking.index)
    }
    mapped["color"] = mapped["cultivo"].map(color_by_crop).fillna("#f2f2f2")

    figure, axes = plt.subplots(1, 2, figsize=(17, 8))
    ranking.sort_values().plot.barh(
        ax=axes[0],
        color=[color_by_crop[crop] for crop in ranking.sort_values().index],
    )
    axes[0].set_title("Diez cultivos con mayor área sembrada acumulada")
    axes[0].set_xlabel("Hectáreas, 2022–2024")
    axes[0].set_ylabel("")
    axes[0].grid(axis="x", alpha=0.22)
    axes[0].ticklabel_format(axis="x", style="plain")

    mapped.plot(
        ax=axes[1],
        color=mapped["color"],
        edgecolor="#bdbdbd",
        linewidth=0.3,
    )
    mapped.dissolve(by="departamento").boundary.plot(
        ax=axes[1],
        color="#525252",
        linewidth=0.9,
    )
    axes[1].set_title(
        "Cultivo con mayor área sembrada acumulada en cada municipio"
    )
    axes[1].set_axis_off()
    axes[1].set_aspect("equal")
    axes[1].legend(
        handles=[
            Patch(facecolor=color_by_crop[crop], label=crop)
            for crop in ranking.index
        ],
        title="Cultivos incluidos",
        loc="lower left",
        frameon=False,
        fontsize=8,
    )
    figure.suptitle(
        "Distribución municipal de los diez cultivos principales, 2022–2024",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "11_mapa_cultivos_principales.png")


def _potato_records(agriculture: pd.DataFrame) -> pd.DataFrame:
    return agriculture[
        agriculture["cultivo"].astype("string").str.casefold().eq("papa")
    ].copy()


def plot_potato_municipal_totals(
    municipalities: gpd.GeoDataFrame,
    agriculture: pd.DataFrame,
) -> None:
    potato = _potato_records(agriculture)
    totals = (
        potato.groupby("codigo_municipio", as_index=False)
        .agg(
            area_sembrada_ha=("area_sembrada_ha", "sum"),
            area_cosechada_ha=("area_cosechada_ha", "sum"),
            produccion_t=("produccion_para_rendimiento_t", "sum"),
            area_rendimiento_ha=("area_para_rendimiento_ha", "sum"),
        )
    )
    totals["rendimiento_ponderado_t_ha"] = (
        totals["produccion_t"] / totals["area_rendimiento_ha"]
    )
    mapped = municipalities.merge(totals, on="codigo_municipio", how="left")
    figure, axes = plt.subplots(2, 2, figsize=(16, 14))
    specifications = [
        (
            "area_sembrada_ha",
            "Área sembrada acumulada",
            "Hectáreas",
            "YlGn",
            True,
        ),
        (
            "area_cosechada_ha",
            "Área cosechada acumulada",
            "Hectáreas",
            "YlGn",
            True,
        ),
        (
            "produccion_t",
            "Producción acumulada",
            "Toneladas",
            "YlOrRd",
            True,
        ),
        (
            "rendimiento_ponderado_t_ha",
            "Rendimiento ponderado",
            "Toneladas/hectárea",
            "PuBuGn",
            False,
        ),
    ]
    for axis, (column, title, label, cmap, logarithmic) in zip(
        axes.flat, specifications
    ):
        _plot_numeric_layer(
            figure,
            axis,
            mapped,
            column=column,
            title=title,
            colorbar_label=label,
            cmap=cmap,
            logarithmic=logarithmic,
        )
    figure.suptitle(
        "Agregado municipal de papa, 2022–2024",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "12_mapa_agregado_municipal_papa.png")


def _label_top_municipalities(
    axis: plt.Axes,
    frame: gpd.GeoDataFrame,
    *,
    column: str,
    count: int = 5,
) -> None:
    top = frame.dropna(subset=[column]).nlargest(count, column).copy()
    points = top.geometry.representative_point()
    offsets = [(-32, -13), (32, -13), (28, 8), (0, 20), (-28, 8)]
    for ((_, row), point, offset) in zip(top.iterrows(), points, offsets):
        axis.annotate(
            str(row["municipio"]).title(),
            (point.x, point.y),
            xytext=offset,
            textcoords="offset points",
            fontsize=6,
            ha="center",
            va="center",
            color="#252525",
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.72,
                "pad": 0.7,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": "#737373",
                "linewidth": 0.35,
            },
        )


def plot_potato_production_by_year(
    municipalities: gpd.GeoDataFrame,
    agriculture: pd.DataFrame,
) -> None:
    potato = _potato_records(agriculture)
    annual = (
        potato.groupby(["codigo_municipio", "anio"], as_index=False)[
            "produccion_para_rendimiento_t"
        ]
        .sum()
        .rename(columns={"produccion_para_rendimiento_t": "produccion_t"})
    )
    positive = annual.loc[annual["produccion_t"].gt(0), "produccion_t"]
    common_norm = LogNorm(vmin=float(positive.min()), vmax=float(positive.max()))
    years = sorted(annual["anio"].dropna().astype(int).unique())
    figure, axes = plt.subplots(1, len(years), figsize=(18, 7))
    for axis, year in zip(np.atleast_1d(axes), years):
        values = annual[annual["anio"].eq(year)].drop(columns="anio")
        mapped = municipalities.merge(values, on="codigo_municipio", how="left")
        _plot_numeric_layer(
            figure,
            axis,
            mapped,
            column="produccion_t",
            title=str(year),
            colorbar_label="Producción de papa (toneladas)",
            cmap="YlOrRd",
            logarithmic=True,
            norm=common_norm,
        )
        _label_top_municipalities(axis, mapped, column="produccion_t")
    figure.suptitle(
        "Producción municipal de papa y cinco municipios principales por año",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "13_mapa_produccion_papa_por_anio.png")


def forecasting_paths() -> tuple[Path, Path]:
    dataset_root = (
        PROCESSED_ROOT
        / "crop_forecasting"
        / "datasets"
        / "version=papa_rendimiento_2026_v1"
    )
    model_root = (
        PROCESSED_ROOT
        / "crop_forecasting"
        / "models"
        / "version=papa_rendimiento_2026_v1"
    )
    return dataset_root, model_root


def plot_yield_history(dataset: pd.DataFrame) -> None:
    history = dataset[
        dataset["anio"].le(2025) & dataset["rendimiento_t_ha"].notna()
    ].copy()
    summary = (
        history.groupby(["departamento", "tipo_periodo", "anio"])[
            "rendimiento_t_ha"
        ]
        .agg(
            mediana="median",
            q25=lambda values: values.quantile(0.25),
            q75=lambda values: values.quantile(0.75),
        )
        .reset_index()
    )
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for axis, period in zip(axes, ["A", "B"]):
        for department, color in DEPARTMENT_COLORS.items():
            selected = summary[
                summary["tipo_periodo"].eq(period)
                & summary["departamento"].eq(department)
            ]
            axis.plot(
                selected["anio"],
                selected["mediana"],
                marker="o",
                color=color,
                linewidth=1.8,
                label=department,
            )
            axis.fill_between(
                selected["anio"].astype(float),
                selected["q25"].astype(float),
                selected["q75"].astype(float),
                color=color,
                alpha=0.14,
            )
        axis.set_title(f"Semestre {period}")
        axis.set_xlabel("Año")
        axis.grid(alpha=0.22)
    axes[0].set_ylabel("Rendimiento de papa (toneladas/hectárea)")
    axes[0].legend(frameon=False)
    figure.suptitle("Rendimiento histórico municipal de papa, 2019–2025")
    figure.tight_layout()
    _save(figure, "06_rendimiento_historico_papa.png")


def plot_dataset_structure(dataset: pd.DataFrame) -> None:
    totals = pd.Series(
        {
            "Clima por semestre": 33,
            "Historia de cultivo": 9,
            "Geografía y tiempo": 3,
            "Identidad y período": 8,
            "Control de filas": 2,
            "Variable objetivo": 1,
        }
    )
    colors = ["#2166ac", "#67a9cf", "#f4a582", "#bdbdbd", "#969696", "#b2182b"]
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    axes[0].barh(totals.index[::-1], totals.values[::-1], color=colors[::-1])
    axes[0].set_xlabel("Columnas")
    axes[0].set_title(f"Estructura de {dataset.shape[1]} columnas")
    axes[0].grid(axis="x", alpha=0.22)
    for position, value in enumerate(totals.values[::-1]):
        axes[0].text(value, position, f" {value}", va="center")

    row_counts = pd.Series(
        {
            "Historia con rendimiento": int(
                (
                    dataset["rendimiento_t_ha"].notna()
                    & dataset["anio"].le(2025)
                ).sum()
            ),
            "Historia sin rendimiento": int(
                (
                    dataset["rendimiento_t_ha"].isna()
                    & dataset["anio"].le(2025)
                ).sum()
            ),
            "2026, municipios de contexto": int(
                (
                    dataset["es_fila_pronostico"]
                    & ~dataset["es_municipio_objetivo"]
                ).sum()
            ),
            "2026, municipios objetivo": int(
                (
                    dataset["es_fila_pronostico"]
                    & dataset["es_municipio_objetivo"]
                ).sum()
            ),
        }
    )
    axes[1].bar(
        row_counts.index,
        row_counts.values,
        color=["#2166ac", "#bdbdbd", "#92c5de", "#b2182b"],
    )
    axes[1].set_ylabel("Filas")
    axes[1].set_title(
        f"Conjunto de datos definitivo: {len(dataset):,} filas".replace(",", ".")
    )
    axes[1].grid(axis="y", alpha=0.22)
    axes[1].tick_params(axis="x", rotation=18)
    for position, value in enumerate(row_counts.values):
        axes[1].text(position, value, f"{value:,}".replace(",", "."), ha="center", va="bottom")
    figure.tight_layout()
    _save(figure, "07_dataset_pronostico.png")


def _model_label(model: object, representation: object) -> str:
    names = {
        "baseline": "Último rendimiento",
        "ridge": "Regresión Ridge",
        "random_forest": "Bosque aleatorio",
        "extra_trees": "Árboles extra",
        "hist_gradient_boosting": "Gradient boosting",
        "mlp": "Red neuronal MLP",
    }
    representations = {
        "lag_1": "último año",
        "media_historica": "promedio histórico",
        "one_hot_entity": "categorías binarias",
        "geo_history": "geografía + historia",
    }
    if str(model) == "baseline" and str(representation) == "media_historica":
        return "Promedio histórico\npromedio histórico"
    representation_label = representations.get(
        str(representation), str(representation)
    )
    return f"{names.get(str(model), str(model))}\n{representation_label}"


def plot_model_metrics(leaderboard: pd.DataFrame) -> None:
    leaderboard = leaderboard.rename(
        columns={
            "model": "modelo",
            "encoding": "representacion",
            "mae_media": "mae",
            "rmse_media": "rmse",
            "smape_media_pct": "smape",
        }
    ).copy()
    leaderboard["etiqueta"] = [
        _model_label(model, representation)
        for model, representation in zip(
            leaderboard["modelo"], leaderboard["representacion"]
        )
    ]
    leaderboard = leaderboard.sort_values("mae", ascending=True)
    positions = np.arange(len(leaderboard))
    colors = [
        "#b2182b" if candidate == "baseline_lag_1" else "#92c5de"
        for candidate in leaderboard["candidate"]
    ]
    figure, axes = plt.subplots(1, 3, figsize=(16, 6), sharey=True)
    metrics = [
        ("mae", "Error absoluto medio\n(toneladas/hectárea)", "Menor es mejor"),
        ("rmse", "Raíz del error cuadrático medio\n(toneladas/hectárea)", "Menor es mejor"),
        ("smape", "Error porcentual absoluto\nsimétrico (%)", "Menor es mejor"),
    ]
    for axis, (column, title, subtitle) in zip(axes, metrics):
        axis.barh(positions, leaderboard[column], color=colors)
        axis.set_title(f"{title}\n{subtitle}")
        axis.grid(axis="x", alpha=0.22)
        for position, value in zip(positions, leaderboard[column]):
            axis.text(value, position, f" {value:.2f}", va="center", fontsize=8)
    axes[0].set_yticks(positions, leaderboard["etiqueta"])
    figure.suptitle("Comparación temporal de métodos sobre 2024–2025")
    figure.tight_layout()
    _save(figure, "08_metricas_modelos.png")


def plot_forecast(forecast: pd.DataFrame) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(15, 12), sharex=True)
    for row, department in enumerate(["Boyacá", "Cundinamarca"]):
        for column, period in enumerate(["A", "B"]):
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
                color="#b2182b",
                ecolor="#92c5de",
                capsize=3,
            )
            axis.set_yticks(positions, selected["municipio"])
            axis.set_title(f"{department} — 2026{period}")
            axis.grid(axis="x", alpha=0.22)
    for axis in axes[-1, :]:
        axis.set_xlabel("Rendimiento pronosticado (toneladas/hectárea)")
    figure.suptitle(
        "Pronóstico de papa 2026 y banda empírica de error del backtesting",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "09_pronostico_papa_2026.png")


def plot_forecast_map(
    municipalities: gpd.GeoDataFrame,
    forecast: pd.DataFrame,
) -> None:
    prediction_column = "prediccion_rendimiento_t_ha"
    norm = Normalize(
        vmin=float(forecast[prediction_column].min()),
        vmax=float(forecast[prediction_column].max()),
    )
    figure, axes = plt.subplots(2, 2, figsize=(15, 13))
    for row, department in enumerate(["Boyacá", "Cundinamarca"]):
        department_map = municipalities[
            municipalities["departamento"].eq(department)
        ]
        for column, period in enumerate(["A", "B"]):
            axis = axes[row, column]
            selected = forecast[
                forecast["departamento"].eq(department)
                & forecast["tipo_periodo"].eq(period)
            ][["codigo_municipio", prediction_column]]
            mapped = department_map.merge(
                selected,
                on="codigo_municipio",
                how="left",
            )
            _plot_numeric_layer(
                figure,
                axis,
                mapped,
                column=prediction_column,
                title=f"{department} — semestre {period}",
                colorbar_label="Rendimiento pronosticado (toneladas/hectárea)",
                cmap="YlGnBu",
                norm=norm,
            )
            targets = mapped[mapped[prediction_column].notna()].copy()
            points = targets.geometry.representative_point()
            axis.scatter(
                points.x,
                points.y,
                s=9,
                color="#252525",
                zorder=3,
            )
            for (_, target), point in zip(targets.iterrows(), points):
                axis.annotate(
                    str(target["municipio"]).title(),
                    (point.x, point.y),
                    xytext=(2, 2),
                    textcoords="offset points",
                    fontsize=5.8,
                    color="#252525",
                )
    figure.suptitle(
        "Rendimiento de papa pronosticado por municipio, 2026",
        fontsize=15,
    )
    figure.tight_layout()
    _save(figure, "14_mapa_pronostico_rendimiento_2026.png")


def main() -> None:
    if not PROCESSED_ROOT.exists():
        raise FileNotFoundError(
            "No existe ECO2026_PROCESSED_ROOT. Defina la variable de entorno "
            "con la raíz eco2026_processed."
        )
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
            "figure.dpi": 120,
        }
    )

    municipalities = load_municipal_geography()

    climate = load_station_climate()
    plot_one_month(climate)
    plot_several_months(climate)
    plot_february_gap(climate)
    stations = load_climate_stations()
    plot_station_locations(municipalities, stations)

    agriculture = load_agriculture()
    plot_crop_periods(agriculture)
    plot_crop_selection(agriculture)
    plot_dominant_crops(municipalities, agriculture)
    plot_potato_municipal_totals(municipalities, agriculture)
    plot_potato_production_by_year(municipalities, agriculture)

    dataset_root, model_root = forecasting_paths()
    dataset = pd.read_parquet(dataset_root / "dataset_definitivo.parquet")
    leaderboard = pd.read_csv(model_root / "leaderboard.csv")
    forecast = pd.read_parquet(model_root / "pronostico_2026.parquet")
    plot_yield_history(dataset)
    plot_dataset_structure(dataset)
    plot_model_metrics(leaderboard)
    plot_forecast(forecast)
    plot_forecast_map(municipalities, forecast)
    print(f"Figuras generadas en {OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
