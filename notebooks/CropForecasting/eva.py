"""Lectura, agregación y selección no anticipativa de municipios EVA."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable
import unicodedata

import pandas as pd

from notebooks.ClimatePipeline.CropMunicipalChange import (
    aggregate_crop_municipal_period,
)


EVA_SHEET = "BasePagina"
EVA_HEADER_ROW = 8
TARGET_CROP = "Papa"
SELECTION_YEARS = (2024, 2025)
TARGET_YEAR = 2026


def _slug(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return text.encode("ascii", errors="ignore").decode("ascii").strip().casefold()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_upra_eva(path: str | Path) -> pd.DataFrame:
    """Lee el contrato oficial UPRA 2019-2025 y valida su cobertura."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(
            f"No existe la fuente EVA UPRA: {source}. "
            "Ejecute el descargador de CropForecasting."
        )
    raw = pd.read_excel(source, sheet_name=EVA_SHEET, header=EVA_HEADER_ROW)
    required = {
        "Código Dane departamento",
        "Código Dane municipio",
        "Cultivo",
        "Año",
        "Periodo",
        "Área sembrada (ha)",
        "Área cosechada (ha)",
        "Producción (t)",
        "Rendimiento (t/ha)",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Faltan columnas en EVA UPRA: {sorted(missing)}")
    years = set(pd.to_numeric(raw["Año"], errors="coerce").dropna().astype(int))
    expected = set(range(2019, 2026))
    if not expected.issubset(years):
        raise ValueError(f"EVA no cubre 2019-2025; años observados: {sorted(years)}")
    return raw


def build_potato_municipal_eva(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Agrega papa por municipio-semestre y devuelve incidencias auditables."""
    result = aggregate_crop_municipal_period(raw, departments=("15", "25"))
    potato = result.municipal_period[
        result.municipal_period["cultivo"].map(_slug).eq(_slug(TARGET_CROP))
    ].copy()
    potato = potato[potato["tipo_periodo"].isin(["A", "B"])].copy()
    potato = potato.sort_values(
        ["codigo_municipio", "anio", "tipo_periodo"]
    ).reset_index(drop=True)
    if potato.duplicated(
        ["codigo_municipio", "anio", "tipo_periodo", "cultivo"]
    ).any():
        raise RuntimeError("EVA papa conserva llaves municipio-año-semestre repetidas.")
    return potato, result.issues


def select_target_municipalities(
    potato: pd.DataFrame,
    *,
    years: Iterable[int] = SELECTION_YEARS,
    top_n_per_department: int = 10,
) -> pd.DataFrame:
    """Selecciona municipios usando solo área sembrada anterior a 2026."""
    selection_years = tuple(sorted({int(year) for year in years}))
    if not selection_years or max(selection_years) >= TARGET_YEAR:
        raise ValueError("La selección territorial solo puede usar años anteriores a 2026.")
    history = potato[potato["anio"].isin(selection_years)].copy()
    ranking = (
        history.groupby(
            [
                "codigo_departamento",
                "departamento",
                "codigo_municipio",
                "municipio",
            ],
            as_index=False,
        )
        .agg(
            area_sembrada_seleccion_ha=("area_sembrada_ha", "sum"),
            observaciones_rendimiento=("rendimiento_t_ha", "count"),
            anios_historia=("anio", "nunique"),
        )
        .sort_values(
            ["codigo_departamento", "area_sembrada_seleccion_ha", "codigo_municipio"],
            ascending=[True, False, True],
        )
    )
    eligible = ranking[
        ranking["anios_historia"].eq(len(selection_years))
        & ranking["observaciones_rendimiento"].ge(2 * len(selection_years))
    ].copy()
    selected = (
        eligible.groupby("codigo_departamento", group_keys=False)
        .head(top_n_per_department)
        .copy()
    )
    selected["ranking_departamento"] = selected.groupby(
        "codigo_departamento"
    ).cumcount() + 1
    selected["anios_seleccion"] = ",".join(map(str, selection_years))
    selected["regla_seleccion"] = "AREA_SEMBRADA_2024_2025_SIN_TARGET_2026"
    counts = selected.groupby("codigo_departamento").size().to_dict()
    if set(counts.values()) != {top_n_per_department} or len(counts) != 2:
        raise RuntimeError(
            f"No fue posible seleccionar {top_n_per_department} municipios "
            f"por departamento: {counts}"
        )
    return selected.reset_index(drop=True)
