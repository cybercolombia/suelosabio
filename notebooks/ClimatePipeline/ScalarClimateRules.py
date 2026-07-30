"""Contratos diarios para presión atmosférica y velocidad del viento."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import unicodedata

import pandas as pd

from ClimateProcessingUtils import PartitionSpec
from TemperatureRules import COLUMNAS_REQUERIDAS, depurar_claves, inferir_cadencias


RULE_VERSION = "escalar_meteorologico_diario_v1"
CONTRATOS_ESCALARES = {
    "presion_atmosferica": {
        "dataset_id": "62tk-nxj5",
        "sensores": {"0255"},
        "unidad": "hpa",
        "descripcion": ("PRESION", "ATMOSFERICA"),
        "rango": (400.0, 1100.0),
        "unidad_salida": "hPa",
    },
    "velocidad_viento": {
        "dataset_id": "sgfv-3yp8",
        "sensores": {"0103"},
        "unidad": "m/s",
        "descripcion": ("VELOCIDAD", "VIENTO"),
        "rango": (0.0, 100.0),
        "unidad_salida": "m/s",
    },
}


@dataclass(slots=True)
class ScalarProcessingResult:
    diario: pd.DataFrame
    cadencias: pd.DataFrame
    rechazados: pd.DataFrame
    conflictos: pd.DataFrame
    duplicados_eliminados: pd.DataFrame
    metricas: dict[str, Any]


def _texto(valor: Any) -> str:
    if pd.isna(valor):
        return ""
    normalized = unicodedata.normalize("NFKD", str(valor))
    return normalized.encode("ascii", errors="ignore").decode("ascii").upper()


def _normalizar(valor: Any) -> Any:
    if pd.isna(valor):
        return pd.NA
    return unicodedata.normalize("NFC", str(valor).strip())


def _agregar_motivo(motivos: pd.Series, mask: pd.Series, reason: str) -> None:
    mask = mask.fillna(False)
    motivos.loc[mask & motivos.ne("")] += "|"
    motivos.loc[mask] += reason


def _contrato(spec: PartitionSpec) -> dict[str, Any]:
    if spec.variable not in CONTRATOS_ESCALARES:
        raise ValueError(f"Variable escalar no soportada: {spec.variable}.")
    contract = CONTRATOS_ESCALARES[spec.variable]
    if spec.dataset_id != contract["dataset_id"]:
        raise ValueError(
            f"{spec.variable} requiere {contract['dataset_id']}; "
            f"se recibió {spec.dataset_id}."
        )
    return contract


def preparar_observaciones(
    raw: pd.DataFrame,
    spec: PartitionSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    contract = _contrato(spec)
    missing = sorted(set(COLUMNAS_REQUERIDAS) - set(raw.columns))
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}.")
    data = raw.loc[:, COLUMNAS_REQUERIDAS].copy()
    data["_orden_origen"] = range(len(data))
    for column in (
        "codigoestacion",
        "codigosensor",
        "dataset_id",
        "departamento",
        "descripcionsensor",
        "municipio",
        "nombreestacion",
        "unidadmedida",
        "zonahidrografica",
    ):
        data[column] = data[column].map(_normalizar).astype("string")
    data["departamento"] = data["departamento"].str.upper().str.replace(
        " ", "_", regex=False
    )
    data["unidadmedida"] = data["unidadmedida"].str.lower()
    data["fechaobservacion"] = pd.to_datetime(data["fechaobservacion"], errors="coerce")
    for column in ("valorobservado", "latitud", "longitud"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    reasons = pd.Series("", index=data.index, dtype="string")
    _agregar_motivo(reasons, data["codigoestacion"].isna(), "estacion_nula")
    _agregar_motivo(reasons, data["codigosensor"].isna(), "sensor_nulo")
    _agregar_motivo(reasons, data["fechaobservacion"].isna(), "fecha_invalida")
    _agregar_motivo(reasons, data["valorobservado"].isna(), "valor_invalido")
    _agregar_motivo(
        reasons,
        data["valorobservado"].notna()
        & ~data["valorobservado"].between(*contract["rango"]),
        "valor_fuera_rango_operativo",
    )
    _agregar_motivo(
        reasons,
        data["unidadmedida"].ne(contract["unidad"]).fillna(True),
        "unidad_fuera_contrato",
    )
    description_valid = data["descripcionsensor"].map(
        lambda value: all(token in _texto(value) for token in contract["descripcion"])
    )
    _agregar_motivo(reasons, ~description_valid, "descripcion_fuera_contrato")
    _agregar_motivo(
        reasons,
        ~data["codigosensor"].isin(contract["sensores"]),
        "sensor_fuera_contrato",
    )
    _agregar_motivo(
        reasons,
        data["dataset_id"].str.lower().ne(spec.dataset_id).fillna(True),
        "fuente_fuera_particion",
    )
    _agregar_motivo(
        reasons,
        data["departamento"].ne(spec.departamento).fillna(True),
        "departamento_fuera_particion",
    )
    valid_date = data["fechaobservacion"].notna()
    _agregar_motivo(
        reasons,
        valid_date & data["fechaobservacion"].dt.year.ne(spec.anio),
        "anio_fuera_particion",
    )
    _agregar_motivo(
        reasons,
        valid_date & data["fechaobservacion"].dt.month.ne(spec.mes),
        "mes_fuera_particion",
    )
    _agregar_motivo(
        reasons,
        data["latitud"].notna() & ~data["latitud"].between(-90, 90),
        "latitud_fuera_rango",
    )
    _agregar_motivo(
        reasons,
        data["longitud"].notna() & ~data["longitud"].between(-180, 180),
        "longitud_fuera_rango",
    )
    rejected = data.loc[reasons.ne("")].copy()
    rejected["motivo_rechazo"] = reasons.loc[reasons.ne("")]
    valid = data.loc[reasons.eq("")].copy()
    return valid.reset_index(drop=True), rejected.reset_index(drop=True)


def _unique_text(values: pd.Series) -> str:
    return " | ".join(sorted(set(values.dropna().astype(str))))


def agregar_diario(
    clean: pd.DataFrame,
    cadences: pd.DataFrame,
    duplicates: pd.DataFrame,
    conflicts: pd.DataFrame,
    spec: PartitionSpec,
) -> pd.DataFrame:
    if clean.empty:
        return pd.DataFrame()
    contract = _contrato(spec)
    data = clean.copy()
    data["fecha"] = data["fechaobservacion"].dt.floor("D")
    keys = ["codigoestacion", "codigosensor", "fecha"]
    daily = (
        data.groupby(keys, as_index=False, dropna=False)
        .agg(
            valor_medio_observado=("valorobservado", "mean"),
            valor_mediano_observado=("valorobservado", "median"),
            valor_minimo_observado=("valorobservado", "min"),
            valor_maximo_observado=("valorobservado", "max"),
            desviacion_estandar_observada=("valorobservado", "std"),
            observaciones_validas=("valorobservado", "size"),
            primera_observacion=("fechaobservacion", "min"),
            ultima_observacion=("fechaobservacion", "max"),
            municipios_observados=("municipio", _unique_text),
            nombres_estacion_observados=("nombreestacion", _unique_text),
            latitud_mediana=("latitud", "median"),
            longitud_mediana=("longitud", "median"),
        )
    )
    daily["amplitud_observada"] = (
        daily["valor_maximo_observado"] - daily["valor_minimo_observado"]
    )
    daily["valor_principal_observado"] = daily["valor_medio_observado"]
    daily["estadistico_principal"] = "MEDIA"
    daily["unidad_valor"] = contract["unidad_salida"]
    daily = daily.merge(cadences, on=keys, how="left")
    daily["cobertura_evaluable"] = (
        daily["cadencia_observada_conocida"].fillna(False).astype(bool)
    )
    daily["observaciones_esperadas"] = (
        86_400 / daily["intervalo_moda_segundos"]
    ).where(daily["cobertura_evaluable"])
    daily["cobertura_observada_pct"] = (
        100 * daily["observaciones_validas"] / daily["observaciones_esperadas"]
    ).round(2).where(daily["cobertura_evaluable"])
    daily["valor_diario"] = pd.Series(pd.NA, index=daily.index, dtype="Float64")
    daily["calidad_dia"] = "PENDIENTE_REGLA_COBERTURA"
    for name, table in (
        ("duplicados_eliminados", duplicates),
        ("conflictos_excluidos", conflicts),
    ):
        if table.empty:
            daily[name] = 0
            continue
        counts = table.copy()
        counts["fecha"] = counts["fechaobservacion"].dt.floor("D")
        counts = counts.groupby(keys).size().reset_index(name=name)
        daily = daily.merge(counts, on=keys, how="left")
        daily[name] = daily[name].fillna(0).astype(int)
    daily.insert(0, "variable", spec.variable)
    daily.insert(1, "dataset_id", spec.dataset_id)
    daily.insert(2, "departamento", spec.departamento)
    daily["regla_version"] = RULE_VERSION
    return daily.sort_values(keys).reset_index(drop=True)


def procesar_escalar(raw: pd.DataFrame, spec: PartitionSpec) -> ScalarProcessingResult:
    contract = _contrato(spec)
    valid, rejected = preparar_observaciones(raw, spec)
    clean, conflicts, duplicates, dedup_metrics = depurar_claves(valid)
    cadences = inferir_cadencias(clean)
    daily = agregar_diario(clean, cadences, duplicates, conflicts, spec)
    metrics = {
        "regla_version": RULE_VERSION,
        "unidad": contract["unidad_salida"],
        "estadistico_principal": "MEDIA",
        "filas_entrada": len(raw),
        "filas_validas_pre_deduplicacion": len(valid),
        "filas_rechazadas": len(rejected),
        **dedup_metrics,
        "filas_depuradas": len(clean),
        "filas_diarias_salida": len(daily),
        "dias_cobertura_no_evaluable": int(
            (~daily["cobertura_evaluable"]).sum()
        )
        if not daily.empty
        else 0,
    }
    return ScalarProcessingResult(
        diario=daily,
        cadencias=cadences,
        rechazados=rejected,
        conflictos=conflicts,
        duplicados_eliminados=duplicates,
        metricas=metrics,
    )
