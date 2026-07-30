"""Agregación agrícola municipal y cambios interanuales auditables."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from .CropYieldProcessing import BUSINESS_KEY, TARGET_KEY, normalize_eva
except ImportError:  # Compatibilidad con notebooks que cargan el módulo directamente.
    from CropYieldProcessing import BUSINESS_KEY, TARGET_KEY, normalize_eva


AGGREGATION_VERSION = "cultivo_municipio_periodo_v1"
CHANGE_VERSION = "cambio_cultivo_municipio_periodo_v1"
GEOGRAPHY_VERSION = "divipola_agricultura_v1"
METRICS = ("area_sembrada_ha", "area_cosechada_ha", "rendimiento_t_ha")


@dataclass(frozen=True)
class CropMunicipalResult:
    municipal_period: pd.DataFrame
    changes: pd.DataFrame
    issues: pd.DataFrame
    summary: pd.DataFrame


@dataclass(frozen=True)
class CropGeographyAudit:
    summary: pd.DataFrame
    crop_without_geometry: pd.DataFrame
    geometry_without_crop: pd.DataFrame
    name_differences: pd.DataFrame


def _period_type(period: pd.Series) -> pd.Series:
    suffix = period.astype("string").str.extract(r"^\d{4}([AB]?)$", expand=False)
    return suffix.replace({"": "ANUAL"}).astype("string")


def _normalized_name(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.normalize("NFKD")
        .str.encode("ascii", errors="ignore")
        .str.decode("ascii")
        .str.upper()
        .str.replace(r"[^A-Z0-9]", "", regex=True)
    )


def _taxonomy_incompatible(data: pd.DataFrame) -> pd.Series:
    taxonomy = (
        data.groupby(TARGET_KEY, dropna=False)
        .agg(
            ciclos=("ciclo_cultivo", "nunique"),
            estados_fisicos=("estado_fisico_cultivo", "nunique"),
        )
        .reset_index()
    )
    keys = taxonomy[
        (taxonomy["ciclos"] > 1) | (taxonomy["estados_fisicos"] > 1)
    ][TARGET_KEY]
    return pd.MultiIndex.from_frame(data[TARGET_KEY]).isin(
        pd.MultiIndex.from_frame(keys)
    )


def _change_status(previous: pd.Series, current: pd.Series) -> pd.Series:
    status = pd.Series("SIN_CAMBIO", index=previous.index, dtype="string")
    status.loc[previous.isna() & current.notna()] = "NUEVO_REGISTRO"
    status.loc[previous.notna() & current.isna()] = "REGISTRO_DESAPARECE"
    status.loc[previous.isna() & current.isna()] = "SIN_DATO"
    status.loc[(previous == 0) & (current > 0)] = "NUEVO_DESDE_CERO"
    status.loc[(previous > 0) & (current == 0)] = "DISMINUYE_A_CERO"
    comparable = previous.notna() & current.notna()
    status.loc[comparable & (current > previous) & ~((previous == 0) & (current > 0))] = (
        "AUMENTA"
    )
    status.loc[comparable & (current < previous) & ~((previous > 0) & (current == 0))] = (
        "DISMINUYE"
    )
    return status


def build_year_over_year_changes(municipal_period: pd.DataFrame) -> pd.DataFrame:
    """Compara únicamente el mismo cultivo y tipo de período entre años consecutivos."""
    required = {*TARGET_KEY, "tipo_periodo", *METRICS}
    missing = required - set(municipal_period)
    if missing:
        raise ValueError(f"Faltan columnas para calcular cambios: {sorted(missing)}")

    years = sorted(int(year) for year in municipal_period["anio"].dropna().unique())
    keys = ["codigo_municipio", "cultivo", "tipo_periodo"]
    identity = ["codigo_departamento", "departamento", "municipio", "ciclo_cultivo"]
    comparisons: list[pd.DataFrame] = []
    for current_year in years:
        previous_year = current_year - 1
        if previous_year not in years:
            continue
        previous = municipal_period.loc[
            municipal_period["anio"] == previous_year, [*keys, *identity, *METRICS]
        ].rename(
            columns={
                **{column: f"{column}_anterior" for column in identity},
                **{metric: f"{metric}_anterior" for metric in METRICS},
            }
        )
        current = municipal_period.loc[
            municipal_period["anio"] == current_year, [*keys, *identity, *METRICS]
        ].rename(columns={metric: f"{metric}_actual" for metric in METRICS})
        comparison = previous.merge(current, on=keys, how="outer", validate="one_to_one")
        for column in identity:
            comparison[column] = comparison[column].fillna(
                comparison.pop(f"{column}_anterior")
            )
        comparison["anio_anterior"] = previous_year
        comparison["anio_actual"] = current_year
        for metric in METRICS:
            old = comparison[f"{metric}_anterior"]
            new = comparison[f"{metric}_actual"]
            comparison[f"{metric}_cambio_abs"] = new - old
            comparison[f"{metric}_cambio_pct"] = np.where(
                old.notna() & new.notna() & old.ne(0),
                100.0 * (new - old) / old.abs(),
                np.nan,
            )
            comparison[f"{metric}_estado"] = _change_status(old, new)
        comparison["change_version"] = CHANGE_VERSION
        comparisons.append(comparison)

    if not comparisons:
        return pd.DataFrame()
    return pd.concat(comparisons, ignore_index=True)


def aggregate_crop_municipal_period(
    raw: pd.DataFrame,
    *,
    departments: Iterable[str] = ("15", "25"),
) -> CropMunicipalResult:
    """Agrega áreas y rendimiento con universos de validez separados por métrica."""
    data = normalize_eva(raw)
    allowed_departments = {str(code).zfill(2) for code in departments}
    data = data[data["codigo_departamento"].isin(allowed_departments)].copy()
    data["tipo_periodo"] = _period_type(data["periodo"])
    expected_year = pd.to_numeric(
        data["periodo"].str.extract(r"^(\d{4})", expand=False), errors="coerce"
    ).astype("Int64")
    cycle = _normalized_name(data["ciclo_cultivo"])
    period_valid = data["periodo"].str.fullmatch(r"\d{4}(?:A|B)?", na=False)
    cycle_period_valid = (
        (cycle.str.contains("TRANSITORI", na=False) & data["tipo_periodo"].isin(["A", "B"]))
        | (cycle.str.contains("PERMANENT", na=False) & data["tipo_periodo"].eq("ANUAL"))
    )
    code_valid = data["codigo_municipio"].str.fullmatch(r"\d{5}", na=False) & (
        data["codigo_municipio"].str[:2] == data["codigo_departamento"]
    )
    taxonomy_incompatible = _taxonomy_incompatible(data)
    business_duplicate = data.duplicated(BUSINESS_KEY, keep=False)

    issue_frames = []
    for mask, reason in [
        (~period_valid, "PERIODO_INVALIDO"),
        (expected_year.ne(data["anio"]), "PERIODO_ANIO_INCONSISTENTE"),
        (~cycle_period_valid, "CICLO_PERIODO_INCOMPATIBLE"),
        (~code_valid, "CODIGO_DANE_INVALIDO"),
        (taxonomy_incompatible, "TAXONOMIA_INCOMPATIBLE"),
        (business_duplicate, "LLAVE_NEGOCIO_DUPLICADA"),
    ]:
        if mask.any():
            issue = data.loc[mask, [*TARGET_KEY, "desagregacion_cultivo"]].copy()
            issue["motivo"] = reason
            issue_frames.append(issue)
    issues = (
        pd.concat(issue_frames, ignore_index=True)
        if issue_frames
        else pd.DataFrame(columns=[*TARGET_KEY, "desagregacion_cultivo", "motivo"])
    )

    usable = (
        period_valid
        & expected_year.eq(data["anio"])
        & cycle_period_valid
        & code_valid
        & ~taxonomy_incompatible
        & ~business_duplicate
    )
    selected = data.loc[usable].copy()

    selected["_area_sembrada"] = selected["area_sembrada_ha"].where(
        selected["area_sembrada_ha"].ge(0)
    )
    selected["_area_cosechada"] = selected["area_cosechada_ha"].where(
        selected["area_cosechada_ha"].ge(0)
    )
    yield_valid = selected["area_cosechada_ha"].gt(0) & selected["produccion_t"].ge(0)
    selected["_cosecha_rendimiento"] = selected["area_cosechada_ha"].where(yield_valid)
    selected["_produccion_rendimiento"] = selected["produccion_t"].where(yield_valid)

    def components(values: pd.Series) -> str:
        return " | ".join(sorted(set(values.dropna().astype(str))))

    municipal = (
        selected.groupby(TARGET_KEY, dropna=False)
        .agg(
            codigo_departamento=("codigo_departamento", "first"),
            departamento=("departamento", "first"),
            municipio=("municipio", "first"),
            ciclo_cultivo=("ciclo_cultivo", "first"),
            estado_fisico_cultivo=("estado_fisico_cultivo", "first"),
            tipo_periodo=("tipo_periodo", "first"),
            area_sembrada_ha=("_area_sembrada", lambda values: values.sum(min_count=1)),
            area_cosechada_ha=("_area_cosechada", lambda values: values.sum(min_count=1)),
            produccion_para_rendimiento_t=(
                "_produccion_rendimiento",
                lambda values: values.sum(min_count=1),
            ),
            area_para_rendimiento_ha=(
                "_cosecha_rendimiento",
                lambda values: values.sum(min_count=1),
            ),
            filas_fuente=("codigo_municipio", "size"),
            filas_siembra=("_area_sembrada", "count"),
            filas_cosecha=("_area_cosechada", "count"),
            filas_rendimiento=("_cosecha_rendimiento", "count"),
            desagregaciones=("desagregacion_cultivo", "nunique"),
            codigos_cultivo=("codigo_cultivo", "nunique"),
            componentes_cultivo=("desagregacion_cultivo", components),
        )
        .reset_index()
    )
    municipal["rendimiento_t_ha"] = (
        municipal["produccion_para_rendimiento_t"]
        / municipal["area_para_rendimiento_ha"].replace(0, np.nan)
    )
    municipal["agregacion_componentes"] = np.where(
        municipal["desagregaciones"] > 1,
        "SUMA_COMPONENTES_DECLARADOS",
        "COMPONENTE_UNICO",
    )
    municipal["requiere_revision_desagregacion"] = municipal["desagregaciones"] > 1
    municipal["aggregation_version"] = AGGREGATION_VERSION
    changes = build_year_over_year_changes(municipal)

    summary = pd.DataFrame(
        [
            {
                "aggregation_version": AGGREGATION_VERSION,
                "filas_entrada": len(data),
                "filas_utilizables": len(selected),
                "targets_municipio_periodo": len(municipal),
                "targets_con_multiples_desagregaciones": int(
                    municipal["requiere_revision_desagregacion"].sum()
                ),
                "filas_cambio_interanual": len(changes),
                "municipios": municipal["codigo_municipio"].nunique(),
                "cultivos": municipal["cultivo"].nunique(),
                "filas_sin_rendimiento": int(municipal["rendimiento_t_ha"].isna().sum()),
                "estado": (
                    "COMPLETA_CON_REVISION_PENDIENTE"
                    if not issues.empty
                    or municipal["requiere_revision_desagregacion"].any()
                    else "COMPLETA"
                ),
            }
        ]
    )
    return CropMunicipalResult(municipal, changes, issues, summary)


def audit_crop_geography(
    municipal_period: pd.DataFrame,
    geography: pd.DataFrame,
) -> CropGeographyAudit:
    """Valida el enlace agrícola-DIVIPOLA exclusivamente por código DANE."""
    code_column = "codigo_municipio_poligono"
    required = {code_column, "municipio_poligono", "departamento_poligono", "geometry"}
    missing = required - set(geography)
    if missing:
        raise ValueError(f"Faltan columnas geográficas: {sorted(missing)}")

    geo = geography.copy()
    geo[code_column] = (
        geo[code_column].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )
    crop_codes = municipal_period[
        ["codigo_municipio", "municipio", "departamento"]
    ].drop_duplicates()
    geometry_codes = geo[
        [code_column, "municipio_poligono", "departamento_poligono"]
    ].drop_duplicates()
    joined = crop_codes.merge(
        geometry_codes,
        left_on="codigo_municipio",
        right_on=code_column,
        how="outer",
        indicator=True,
    )
    crop_without = joined.loc[joined["_merge"] == "left_only"].copy()
    geometry_without = joined.loc[joined["_merge"] == "right_only"].copy()
    both = joined.loc[joined["_merge"] == "both"].copy()
    name_difference = both.loc[
        (_normalized_name(both["municipio"]) != _normalized_name(both["municipio_poligono"]))
        | (
            _normalized_name(both["departamento"])
            != _normalized_name(both["departamento_poligono"])
        )
    ].copy()

    crs = getattr(geography, "crs", None)
    valid_geometry = getattr(geography, "is_valid", pd.Series(True, index=geo.index))
    empty_geometry = getattr(geography, "is_empty", pd.Series(False, index=geo.index))
    summary = pd.DataFrame(
        [
            {
                "geography_version": GEOGRAPHY_VERSION,
                "municipios_agricultura": crop_codes["codigo_municipio"].nunique(),
                "poligonos": len(geo),
                "codigos_poligono_unicos": geo[code_column].nunique(),
                "codigos_poligono_duplicados": int(geo[code_column].duplicated().sum()),
                "municipios_sin_geometria": len(crop_without),
                "geometrias_sin_agricultura": len(geometry_without),
                "geometrias_invalidas": int((~pd.Series(valid_geometry)).sum()),
                "geometrias_vacias": int(pd.Series(empty_geometry).sum()),
                "diferencias_nombre_con_codigo_coincidente": len(name_difference),
                "crs": str(crs) if crs is not None else None,
                "estado": (
                    "COMPLETA"
                    if crop_without.empty
                    and geometry_without.empty
                    and not geo[code_column].duplicated().any()
                    and pd.Series(valid_geometry).all()
                    and not pd.Series(empty_geometry).any()
                    else "COMPLETA_CON_REVISION_PENDIENTE"
                ),
            }
        ]
    )
    return CropGeographyAudit(summary, crop_without, geometry_without, name_difference)


def join_changes_to_geography(
    changes: pd.DataFrame,
    geography: pd.DataFrame,
) -> pd.DataFrame:
    """Une cambios a polígonos; conserva la clase GeoDataFrame si está disponible."""
    geo = geography.copy()
    geo["codigo_municipio_poligono"] = geo["codigo_municipio_poligono"].astype("string")
    return geo.merge(
        changes,
        left_on="codigo_municipio_poligono",
        right_on="codigo_municipio",
        how="inner",
        validate="one_to_many",
    )
