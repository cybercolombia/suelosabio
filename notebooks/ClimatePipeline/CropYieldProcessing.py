"""Auditoría y curación reproducible de registros agrícolas EVA."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Iterable

import numpy as np
import pandas as pd


AUDIT_VERSION = "auditoria_eva_cruda_v1"
CURATION_VERSION = "eva_curada_v1"
CURATED_AUDIT_VERSION = "auditoria_eva_curada_v1"

COLUMN_ALIASES = {
    "Código Dane departamento": "codigo_departamento",
    "Departamento": "departamento",
    "Código Dane municipio": "codigo_municipio",
    "Municipio": "municipio",
    "Grupo cultivo": "grupo_cultivo",
    "Subgrupo": "subgrupo",
    "Cultivo": "cultivo",
    "Desagregación cultivo": "desagregacion_cultivo",
    "Año": "anio",
    "Periodo": "periodo",
    "Área sembrada (ha)": "area_sembrada_ha",
    "Área cosechada (ha)": "area_cosechada_ha",
    "Producción (t)": "produccion_t",
    "Rendimiento (t/ha)": "rendimiento_publicado_t_ha",
    "Ciclo del cultivo": "ciclo_cultivo",
    "Estado físico del cultivo": "estado_fisico_cultivo",
    "Código del cultivo": "codigo_cultivo",
    "Nombre científico del cultivo": "nombre_cientifico_cultivo",
    "c_digo_dane_departamento": "codigo_departamento",
    "departamento": "departamento",
    "c_digo_dane_municipio": "codigo_municipio",
    "municipio": "municipio",
    "grupo_cultivo": "grupo_cultivo",
    "subgrupo": "subgrupo",
    "cultivo": "cultivo",
    "desagregaci_n_cultivo": "desagregacion_cultivo",
    "a_o": "anio",
    "periodo": "periodo",
    "rea_sembrada": "area_sembrada_ha",
    "rea_cosechada": "area_cosechada_ha",
    "producci_n": "produccion_t",
    "rendimiento": "rendimiento_publicado_t_ha",
    "ciclo_del_cultivo": "ciclo_cultivo",
    "estado_f_sico_del_cultivo": "estado_fisico_cultivo",
    "c_digo_del_cultivo": "codigo_cultivo",
    "nombre_cient_fico_del_cultivo": "nombre_cientifico_cultivo",
    "dataset_id": "dataset_id",
}

REQUIRED_COLUMNS = {
    "codigo_departamento",
    "departamento",
    "codigo_municipio",
    "municipio",
    "cultivo",
    "desagregacion_cultivo",
    "anio",
    "periodo",
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_publicado_t_ha",
    "ciclo_cultivo",
    "estado_fisico_cultivo",
}

BUSINESS_KEY = [
    "codigo_municipio",
    "anio",
    "periodo",
    "cultivo",
    "desagregacion_cultivo",
    "ciclo_cultivo",
    "estado_fisico_cultivo",
]
TARGET_KEY = ["codigo_municipio", "anio", "periodo", "cultivo"]
MEASURE_COLUMNS = [
    "area_sembrada_ha",
    "area_cosechada_ha",
    "produccion_t",
    "rendimiento_publicado_t_ha",
]
DEPARTMENT_CODES = {"15": "BOYACÁ", "25": "CUNDINAMARCA"}


@dataclass(frozen=True)
class RawAuditResult:
    normalized: pd.DataFrame
    summary: pd.DataFrame
    missingness: pd.DataFrame
    duplicate_keys: pd.DataFrame
    quality_flags: pd.DataFrame
    coverage: pd.DataFrame


@dataclass(frozen=True)
class CurationResult:
    curated: pd.DataFrame
    exclusions: pd.DataFrame
    reconciliation: pd.DataFrame
    summary: pd.DataFrame


def _slug(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    return re.sub(
        r"[^a-z0-9]+",
        "_",
        text.encode("ascii", errors="ignore").decode("ascii").lower(),
    ).strip("_")


def _text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def normalize_eva(raw: pd.DataFrame) -> pd.DataFrame:
    """Homologa el esquema Socrata sin modificar el DataFrame de entrada."""
    renamed = raw.rename(
        columns={source: target for source, target in COLUMN_ALIASES.items() if source in raw}
    ).copy()
    missing = REQUIRED_COLUMNS - set(renamed.columns)
    if missing:
        raise ValueError(f"Faltan columnas EVA obligatorias: {sorted(missing)}")

    for column in [
        "departamento",
        "municipio",
        "cultivo",
        "desagregacion_cultivo",
        "grupo_cultivo",
        "subgrupo",
        "ciclo_cultivo",
        "estado_fisico_cultivo",
        "codigo_cultivo",
        "nombre_cientifico_cultivo",
        "dataset_id",
    ]:
        if column in renamed:
            renamed[column] = _text(renamed[column])

    renamed["codigo_departamento"] = (
        _text(renamed["codigo_departamento"]).str.replace(r"\.0$", "", regex=True).str.zfill(2)
    )
    renamed["codigo_municipio"] = (
        _text(renamed["codigo_municipio"]).str.replace(r"\.0$", "", regex=True).str.zfill(5)
    )
    renamed["anio"] = pd.to_numeric(renamed["anio"], errors="coerce").astype("Int64")
    renamed["periodo"] = _text(renamed["periodo"]).str.upper()
    for column in MEASURE_COLUMNS:
        renamed[column] = pd.to_numeric(renamed[column], errors="coerce").astype("Float64")
    return renamed


def _quality_flags(data: pd.DataFrame) -> pd.DataFrame:
    calculated = data["produccion_t"] / data["area_cosechada_ha"].replace(0, pd.NA)
    difference = (data["rendimiento_publicado_t_ha"] - calculated).abs()
    cycle = data["ciclo_cultivo"].map(_slug)
    annual = data["periodo"].str.fullmatch(r"\d{4}", na=False)
    semester = data["periodo"].str.fullmatch(r"\d{4}[AB]", na=False)
    expected_year = data["periodo"].str.extract(r"^(\d{4})", expand=False)

    return pd.DataFrame(
        {
            "fila": data.index,
            "codigo_municipio": data["codigo_municipio"],
            "anio": data["anio"],
            "periodo": data["periodo"],
            "cultivo": data["cultivo"],
            "codigo_departamento_invalido": ~data["codigo_departamento"].isin(DEPARTMENT_CODES),
            "codigo_municipio_invalido": ~data["codigo_municipio"].str.fullmatch(
                r"\d{5}", na=False
            ),
            "codigo_municipio_departamento_inconsistente": (
                data["codigo_municipio"].str.slice(0, 2)
                != data["codigo_departamento"]
            ).fillna(True),
            "periodo_invalido": ~(annual | semester),
            "periodo_anio_inconsistente": pd.to_numeric(
                expected_year, errors="coerce"
            ).astype("Int64")
            != data["anio"],
            "ciclo_periodo_sospechoso": (
                (cycle.str.contains("transitori", na=False) & ~semester)
                | (cycle.str.contains("permanent", na=False) & ~annual)
            ),
            "medida_negativa": data[MEASURE_COLUMNS].lt(0).any(axis=1),
            "cosecha_mayor_siembra": data["area_cosechada_ha"]
            > data["area_sembrada_ha"],
            "area_cosechada_no_positiva": data["area_cosechada_ha"].fillna(0) <= 0,
            "rendimiento_formula_difiere": difference.fillna(np.inf) > 0.01,
            "diferencia_rendimiento_abs": difference,
        }
    )


def audit_raw_eva(raw: pd.DataFrame) -> RawAuditResult:
    data = normalize_eva(raw)
    flags = _quality_flags(data)
    flag_columns = [
        column
        for column in flags.columns
        if column not in {"fila", *TARGET_KEY, "diferencia_rendimiento_abs"}
    ]
    duplicate_mask = data.duplicated(BUSINESS_KEY, keep=False)
    duplicate_keys = (
        data.loc[duplicate_mask]
        .groupby(BUSINESS_KEY, dropna=False)
        .size()
        .rename("filas")
        .reset_index()
        .sort_values("filas", ascending=False)
    )
    missingness = pd.DataFrame(
        {
            "columna": data.columns,
            "nulos": [int(data[column].isna().sum()) for column in data],
            "porcentaje_nulos": [
                round(float(data[column].isna().mean() * 100), 4) for column in data
            ],
        }
    )
    coverage = (
        data.groupby(["departamento", "anio", "periodo", "cultivo"], dropna=False)
        .agg(
            filas=("codigo_municipio", "size"),
            municipios=("codigo_municipio", "nunique"),
            rendimiento_valido=("rendimiento_publicado_t_ha", "count"),
        )
        .reset_index()
    )
    summary = pd.DataFrame(
        [
            {
                "audit_version": AUDIT_VERSION,
                "filas": len(data),
                "columnas": len(data.columns),
                "departamentos": data["codigo_departamento"].nunique(),
                "municipios": data["codigo_municipio"].nunique(),
                "anios": data["anio"].nunique(),
                "periodos": data["periodo"].nunique(),
                "cultivos": data["cultivo"].nunique(),
                "duplicados_exactos": int(data.duplicated().sum()),
                "filas_en_llaves_duplicadas": int(duplicate_mask.sum()),
                **{f"filas_{column}": int(flags[column].sum()) for column in flag_columns},
            }
        ]
    )
    return RawAuditResult(data, summary, missingness, duplicate_keys, flags, coverage)


def curate_eva(
    raw: pd.DataFrame,
    *,
    departments: Iterable[str] = ("BOYACÁ", "CUNDINAMARCA"),
    crops: Iterable[str] | None = None,
) -> CurationResult:
    data = normalize_eva(raw)
    allowed_departments = {_slug(value) for value in departments}
    selected = data[data["departamento"].map(_slug).isin(allowed_departments)].copy()
    if crops is not None:
        allowed_crops = {_slug(value) for value in crops}
        selected = selected[selected["cultivo"].map(_slug).isin(allowed_crops)].copy()

    flags = _quality_flags(selected).set_index("fila")
    selected["_invalid_measure"] = (
        flags["medida_negativa"]
        | flags["area_cosechada_no_positiva"]
        | flags["periodo_invalido"]
        | flags["periodo_anio_inconsistente"]
    )
    taxonomy = (
        selected.groupby(TARGET_KEY, dropna=False)
        .agg(
            ciclos=("ciclo_cultivo", "nunique"),
            estados_fisicos=("estado_fisico_cultivo", "nunique"),
        )
        .reset_index()
    )
    incompatible_keys = taxonomy[
        (taxonomy["ciclos"] > 1) | (taxonomy["estados_fisicos"] > 1)
    ][TARGET_KEY]
    incompatible_index = pd.MultiIndex.from_frame(incompatible_keys)
    selected_index = pd.MultiIndex.from_frame(selected[TARGET_KEY])
    selected["_taxonomy_incompatible"] = selected_index.isin(incompatible_index)

    reason = pd.Series(pd.NA, index=selected.index, dtype="string")
    reason.loc[selected["_invalid_measure"]] = "MEDIDA_O_PERIODO_INVALIDO"
    reason.loc[selected["_taxonomy_incompatible"]] = "TAXONOMIA_INCOMPATIBLE"
    exclusions = selected.loc[reason.notna()].copy()
    exclusions["motivo_exclusion"] = reason.loc[reason.notna()]
    valid = selected.loc[reason.isna()].copy()

    curated = (
        valid.groupby(TARGET_KEY, dropna=False)
        .agg(
            codigo_departamento=("codigo_departamento", "first"),
            departamento=("departamento", "first"),
            municipio=("municipio", "first"),
            ciclo_cultivo=("ciclo_cultivo", "first"),
            estado_fisico_cultivo=("estado_fisico_cultivo", "first"),
            area_sembrada_ha=("area_sembrada_ha", "sum"),
            area_cosechada_ha=("area_cosechada_ha", "sum"),
            produccion_t=("produccion_t", "sum"),
            filas_fuente=("codigo_municipio", "size"),
            desagregaciones=("desagregacion_cultivo", "nunique"),
            rendimiento_publicado_ponderado_t_ha=(
                "rendimiento_publicado_t_ha",
                lambda values: np.nan,
            ),
        )
        .reset_index()
    )
    weighted = (
        valid.assign(
            _weighted=valid["rendimiento_publicado_t_ha"] * valid["area_cosechada_ha"]
        )
        .groupby(TARGET_KEY, dropna=False)["_weighted"]
        .sum(min_count=1)
        / valid.groupby(TARGET_KEY, dropna=False)["area_cosechada_ha"].sum(min_count=1)
    ).rename("rendimiento_publicado_ponderado_t_ha")
    curated = curated.drop(columns="rendimiento_publicado_ponderado_t_ha").merge(
        weighted.reset_index(), on=TARGET_KEY, how="left", validate="one_to_one"
    )
    curated["rendimiento_t_ha"] = (
        curated["produccion_t"] / curated["area_cosechada_ha"]
    )
    curated["diferencia_rendimiento_publicado_abs"] = (
        curated["rendimiento_t_ha"]
        - curated["rendimiento_publicado_ponderado_t_ha"]
    ).abs()
    curated["metodologia_desde_2022"] = curated["anio"] >= 2022
    curated["calidad_target"] = np.where(
        curated["diferencia_rendimiento_publicado_abs"] <= 0.01,
        "CONSISTENTE",
        "REVISAR_DIFERENCIA_PUBLICADA",
    )
    curated["curation_version"] = CURATION_VERSION

    reconciliation = (
        pd.DataFrame(
            [
                {"concepto": "filas_entrada", "filas": len(data)},
                {"concepto": "filas_territorio_cultivo", "filas": len(selected)},
                {"concepto": "filas_excluidas", "filas": len(exclusions)},
                {"concepto": "filas_validas_consolidadas", "filas": len(valid)},
                {"concepto": "targets_curados", "filas": len(curated)},
            ]
        )
    )
    summary = (
        curated.groupby(["departamento", "anio", "periodo", "cultivo"], dropna=False)
        .agg(
            targets=("codigo_municipio", "size"),
            municipios=("codigo_municipio", "nunique"),
            area_cosechada_ha=("area_cosechada_ha", "sum"),
            produccion_t=("produccion_t", "sum"),
            rendimiento_mediano_t_ha=("rendimiento_t_ha", "median"),
        )
        .reset_index()
    )
    return CurationResult(curated, exclusions, reconciliation, summary)


def audit_curated_eva(curated: pd.DataFrame) -> dict[str, pd.DataFrame]:
    missing = REQUIRED_COLUMNS.intersection(
        {"codigo_municipio", "anio", "periodo", "cultivo"}
    ) - set(curated.columns)
    if missing:
        raise ValueError(f"Faltan columnas curadas: {sorted(missing)}")
    duplicate_keys = curated[curated.duplicated(TARGET_KEY, keep=False)].copy()
    formula = curated["produccion_t"] / curated["area_cosechada_ha"].replace(0, pd.NA)
    row_checks = curated[TARGET_KEY].copy()
    row_checks["llave_nula"] = curated[TARGET_KEY].isna().any(axis=1)
    row_checks["medida_no_finita"] = ~np.isfinite(
        curated[["area_cosechada_ha", "produccion_t", "rendimiento_t_ha"]]
        .astype(float)
    ).all(axis=1)
    row_checks["formula_inconsistente"] = (
        curated["rendimiento_t_ha"] - formula
    ).abs().fillna(np.inf) > 1e-9
    coverage = (
        curated.groupby(["departamento", "anio", "periodo", "cultivo"], dropna=False)
        .agg(
            targets=("codigo_municipio", "size"),
            municipios=("codigo_municipio", "nunique"),
            rendimiento_min=("rendimiento_t_ha", "min"),
            rendimiento_mediana=("rendimiento_t_ha", "median"),
            rendimiento_max=("rendimiento_t_ha", "max"),
        )
        .reset_index()
    )
    summary = pd.DataFrame(
        [
            {
                "audit_version": CURATED_AUDIT_VERSION,
                "filas": len(curated),
                "llaves_duplicadas": len(duplicate_keys),
                "filas_llave_nula": int(row_checks["llave_nula"].sum()),
                "filas_medida_no_finita": int(row_checks["medida_no_finita"].sum()),
                "filas_formula_inconsistente": int(
                    row_checks["formula_inconsistente"].sum()
                ),
                "estado": (
                    "COMPLETA"
                    if duplicate_keys.empty and not row_checks.iloc[:, 4:].any().any()
                    else "COMPLETA_CON_REVISION_PENDIENTE"
                ),
            }
        ]
    )
    return {
        "summary": summary,
        "row_checks": row_checks,
        "duplicate_keys": duplicate_keys,
        "coverage": coverage,
    }
