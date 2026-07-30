"""Consolidación diaria común para temperatura, presión y viento."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


CONSOLIDATION_VERSION = "variable_escalar_estacion_dia_v1"
CLAVE_SENSOR_DIA = ("departamento", "codigoestacion", "codigosensor", "fecha")
CLAVE_ESTACION_DIA = ("departamento", "codigoestacion", "fecha")
VARIABLES_SOPORTADAS = {
    "temperatura_ambiente": ("temperatura_principal_observada_c", "°C", 1.0),
    "temperatura_minima": ("temperatura_principal_observada_c", "°C", 1.0),
    "temperatura_maxima": ("temperatura_principal_observada_c", "°C", 1.0),
    "presion_atmosferica": ("valor_principal_observado", "hPa", 2.0),
    "velocidad_viento": ("valor_principal_observado", "m/s", 1.0),
}


@dataclass(slots=True)
class ScalarDailyConsolidationResult:
    diario_estacion: pd.DataFrame
    candidatos_sensor: pd.DataFrame
    metricas: dict[str, Any]


def _unicos(serie: pd.Series) -> str:
    return " | ".join(sorted(set(serie.dropna().astype(str))))


def _mediana(serie: pd.Series) -> Any:
    valores = pd.to_numeric(serie, errors="coerce").dropna()
    return valores.median() if not valores.empty else pd.NA


def _validar_calendario(calendario: pd.DataFrame) -> tuple[pd.DataFrame, str, str, float]:
    base = {
        "variable",
        "dataset_id",
        *CLAVE_SENSOR_DIA,
        "es_dia_observado",
        "cobertura_observada_pct",
        "cobertura_evaluable",
        "municipios_observados",
        "nombres_estacion_observados",
        "latitud_mediana",
        "longitud_mediana",
    }
    faltantes = sorted(base - set(calendario.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del calendario escalar: {faltantes}.")
    variables = set(calendario["variable"].dropna().astype(str))
    if len(variables) != 1:
        raise ValueError("El calendario debe contener exactamente una variable.")
    variable = variables.pop()
    if variable not in VARIABLES_SOPORTADAS:
        raise ValueError(f"Variable escalar no soportada: {variable}.")
    columna_valor, unidad, tolerancia = VARIABLES_SOPORTADAS[variable]
    if columna_valor not in calendario.columns:
        raise ValueError(f"Falta la columna observada {columna_valor}.")
    tabla = calendario.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    if tabla["fecha"].isna().any():
        raise ValueError("El calendario contiene fechas inválidas.")
    if tabla.duplicated(list(CLAVE_SENSOR_DIA)).any():
        raise ValueError("El calendario contiene llaves sensor-día repetidas.")
    observado = tabla["es_dia_observado"].astype("boolean").fillna(False)
    if tabla.loc[observado, columna_valor].isna().any():
        raise ValueError("Hay días observados sin valor escalar.")
    return tabla, columna_valor, unidad, tolerancia


def consolidar_escalar_diario(
    calendario: pd.DataFrame,
    valores_sospechosos: pd.DataFrame | None = None,
    *,
    cobertura_minima_pct: float = 90.0,
    cobertura_maxima_pct: float = 102.0,
    tolerancia_sensores: float | None = None,
) -> ScalarDailyConsolidationResult:
    """Acepta solo observaciones con cobertura válida y sensores concordantes."""
    if not 0 <= cobertura_minima_pct <= cobertura_maxima_pct:
        raise ValueError("La ventana de cobertura es inválida.")
    tabla, columna_valor, unidad, tolerancia_default = _validar_calendario(
        calendario
    )
    tolerancia = (
        tolerancia_default
        if tolerancia_sensores is None
        else float(tolerancia_sensores)
    )
    if tolerancia < 0:
        raise ValueError("La tolerancia entre sensores no puede ser negativa.")

    claves = list(CLAVE_SENSOR_DIA)
    sospechosos = valores_sospechosos
    if sospechosos is None or sospechosos.empty:
        tabla["motivos_revision"] = pd.NA
    else:
        faltantes = sorted(set(claves) - set(sospechosos.columns))
        if faltantes:
            raise ValueError(
                f"Faltan llaves de valores sospechosos: {faltantes}."
            )
        revision = sospechosos.copy()
        revision["fecha"] = pd.to_datetime(revision["fecha"], errors="coerce")
        if "motivos_revision" not in revision:
            revision["motivos_revision"] = "VALOR_SOSPECHOSO"
        revision = (
            revision.groupby(claves, as_index=False)["motivos_revision"]
            .agg(_unicos)
        )
        tabla = tabla.merge(revision, on=claves, how="left", validate="one_to_one")

    observado = tabla["es_dia_observado"].astype("boolean").fillna(False)
    evaluable = tabla["cobertura_evaluable"].astype("boolean").fillna(False)
    cobertura = pd.to_numeric(tabla["cobertura_observada_pct"], errors="coerce")
    tabla["estado_candidato_sensor"] = "CANDIDATO_VALIDO"
    tabla.loc[~observado, "estado_candidato_sensor"] = "SIN_OBSERVACION"
    tabla.loc[observado & ~evaluable, "estado_candidato_sensor"] = (
        "COBERTURA_NO_EVALUABLE"
    )
    tabla.loc[
        observado & evaluable & cobertura.lt(cobertura_minima_pct),
        "estado_candidato_sensor",
    ] = "COBERTURA_BAJA"
    tabla.loc[
        observado & evaluable & cobertura.gt(cobertura_maxima_pct),
        "estado_candidato_sensor",
    ] = "COBERTURA_EXCESIVA"
    tabla.loc[
        observado & tabla["motivos_revision"].notna(),
        "estado_candidato_sensor",
    ] = "VALOR_SOSPECHOSO"
    tabla["es_candidato_valido"] = tabla["estado_candidato_sensor"].eq(
        "CANDIDATO_VALIDO"
    )

    filas: list[dict[str, Any]] = []
    for clave, grupo in tabla.groupby(list(CLAVE_ESTACION_DIA), sort=True):
        validos = grupo.loc[grupo["es_candidato_valido"]]
        observados = grupo.loc[
            grupo["es_dia_observado"].astype("boolean").fillna(False)
        ]
        diferencia = (
            validos[columna_valor].max() - validos[columna_valor].min()
            if len(validos) > 1
            else 0.0 if len(validos) == 1 else pd.NA
        )
        concordantes = (
            not validos.empty
            and (len(validos) == 1 or float(diferencia) <= tolerancia)
        )
        if concordantes:
            valor = _mediana(validos[columna_valor])
            calidad = (
                "VALIDO_SENSOR_UNICO"
                if len(validos) == 1
                else "VALIDO_SENSORES_CONCORDANTES"
            )
        elif validos.empty:
            valor = pd.NA
            calidad = (
                "SIN_OBSERVACION"
                if observados.empty
                else "SIN_SENSOR_VALIDO"
            )
        else:
            valor = pd.NA
            calidad = "SENSORES_DISCREPANTES"
        metadatos = observados if not observados.empty else grupo
        filas.append(
            {
                "variable": grupo["variable"].iloc[0],
                "dataset_id": grupo["dataset_id"].iloc[0],
                "departamento": clave[0],
                "codigoestacion": clave[1],
                "fecha": clave[2],
                "valor_diario": valor,
                "unidad_valor": unidad,
                "sensores_observados": _unicos(observados["codigosensor"]),
                "sensores_validos": _unicos(validos["codigosensor"]),
                "numero_sensores_observados": len(observados),
                "numero_sensores_validos": len(validos),
                "diferencia_sensores": diferencia,
                "cobertura_mediana_sensores_pct": _mediana(
                    validos["cobertura_observada_pct"]
                ),
                "es_dia_faltante": observados.empty,
                "calidad_dia": calidad,
                "requiere_revision": calidad not in {
                    "VALIDO_SENSOR_UNICO",
                    "VALIDO_SENSORES_CONCORDANTES",
                    "SIN_OBSERVACION",
                },
                "motivos_revision": _unicos(observados["motivos_revision"]),
                "municipios_observados": _unicos(
                    metadatos["municipios_observados"]
                ),
                "nombres_estacion_observados": _unicos(
                    metadatos["nombres_estacion_observados"]
                ),
                "latitud_mediana": _mediana(metadatos["latitud_mediana"]),
                "longitud_mediana": _mediana(metadatos["longitud_mediana"]),
                "regla_consolidacion": CONSOLIDATION_VERSION,
            }
        )
    diario = pd.DataFrame(filas)
    if not diario.empty:
        diario["valor_diario"] = diario["valor_diario"].astype("Float64")
        diario = diario.sort_values(list(CLAVE_ESTACION_DIA)).reset_index(drop=True)
    metricas = {
        "regla_version": CONSOLIDATION_VERSION,
        "variable": tabla["variable"].iloc[0],
        "unidad": unidad,
        "filas_calendario_entrada": len(tabla),
        "filas_estacion_dia_salida": len(diario),
        "dias_aceptados": int(diario["valor_diario"].notna().sum()),
        "dias_sin_observacion": int(diario["es_dia_faltante"].sum()),
        "dias_sensores_discrepantes": int(
            diario["calidad_dia"].eq("SENSORES_DISCREPANTES").sum()
        ),
        "cobertura_minima_pct": float(cobertura_minima_pct),
        "cobertura_maxima_pct": float(cobertura_maxima_pct),
        "tolerancia_sensores": tolerancia,
    }
    return ScalarDailyConsolidationResult(diario, tabla, metricas)
