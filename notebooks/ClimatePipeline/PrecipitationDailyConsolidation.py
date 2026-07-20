"""Consolidacion trazable de precipitacion a una fila por estacion y dia."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import pandas as pd


CONSOLIDATION_VERSION = "precipitacion_estacion_dia_v1"
CLAVE_SENSOR_DIA = ("departamento", "codigoestacion", "codigosensor", "fecha")
CLAVE_ESTACION_DIA = ("departamento", "codigoestacion", "fecha")
COLUMNAS_CALENDARIO_REQUERIDAS = (
    "variable",
    "dataset_id",
    "departamento",
    "codigoestacion",
    "codigosensor",
    "fecha",
    "es_dia_observado",
    "precipitacion_observada_mm",
    "cobertura_observada_pct",
    "cobertura_evaluable",
    "municipios_observados",
    "nombres_estacion_observados",
    "latitud_mediana",
    "longitud_mediana",
)


@dataclass(slots=True)
class DailyConsolidationResult:
    diario_estacion: pd.DataFrame
    candidatos_sensor: pd.DataFrame
    sensores_cuarentena: pd.DataFrame
    metricas: dict[str, Any]


def _unicos_texto(serie: pd.Series) -> str:
    return " | ".join(sorted(set(serie.dropna().astype(str))))


def _mediana_numerica(serie: pd.Series) -> Any:
    valores = pd.to_numeric(serie, errors="coerce").dropna()
    return valores.median() if not valores.empty else pd.NA


def validar_calendario(calendario: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_CALENDARIO_REQUERIDAS) - set(calendario.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del calendario auditado: {faltantes}.")

    tabla = calendario.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    if tabla["fecha"].isna().any():
        raise ValueError("El calendario contiene fechas invalidas.")
    if tabla.duplicated(list(CLAVE_SENSOR_DIA)).any():
        raise ValueError("El calendario contiene llaves estacion-sensor-dia repetidas.")
    observados = tabla["es_dia_observado"].fillna(False)
    if tabla.loc[observados, "precipitacion_observada_mm"].isna().any():
        raise ValueError("Hay dias observados sin precipitacion observada.")
    if tabla.loc[~observados, "precipitacion_observada_mm"].notna().any():
        raise ValueError("Hay dias ausentes con precipitacion observada.")
    return tabla


def identificar_sensores_cuarentena(
    valores_sospechosos: pd.DataFrame,
    minimo_dias_persistentes: int = 3,
) -> pd.DataFrame:
    columnas = [
        "departamento",
        "codigoestacion",
        "codigosensor",
        "dias_evidencia",
        "primera_fecha_evidencia",
        "ultima_fecha_evidencia",
        "motivo_cuarentena",
    ]
    if minimo_dias_persistentes <= 0:
        raise ValueError("minimo_dias_persistentes debe ser positivo.")
    if valores_sospechosos.empty:
        return pd.DataFrame(columns=columnas)

    requeridas = set(CLAVE_SENSOR_DIA) | {"motivos_revision"}
    faltantes = sorted(requeridas - set(valores_sospechosos.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas de valores sospechosos: {faltantes}.")

    tabla = valores_sospechosos.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    persistentes = tabla.loc[
        tabla["motivos_revision"].astype("string").str.contains(
            "POSITIVOS_PERSISTENTES",
            regex=False,
            na=False,
        )
    ]
    if persistentes.empty:
        return pd.DataFrame(columns=columnas)

    cuarentena = (
        persistentes.groupby(
            ["departamento", "codigoestacion", "codigosensor"],
            as_index=False,
        )
        .agg(
            dias_evidencia=("fecha", "nunique"),
            primera_fecha_evidencia=("fecha", "min"),
            ultima_fecha_evidencia=("fecha", "max"),
        )
    )
    cuarentena = cuarentena.loc[
        cuarentena["dias_evidencia"].ge(minimo_dias_persistentes)
    ].copy()
    cuarentena["motivo_cuarentena"] = "PATRON_POSITIVO_PERSISTENTE"
    return cuarentena[columnas].reset_index(drop=True)


def clasificar_candidatos_sensor(
    calendario: pd.DataFrame,
    valores_sospechosos: pd.DataFrame,
    sensores_cuarentena: pd.DataFrame,
    cobertura_minima_pct: float = 90.0,
    cobertura_maxima_pct: float = 102.0,
) -> pd.DataFrame:
    if not 0 <= cobertura_minima_pct <= cobertura_maxima_pct:
        raise ValueError("La ventana de cobertura es invalida.")

    tabla = calendario.copy()
    claves = list(CLAVE_SENSOR_DIA)
    if valores_sospechosos.empty:
        tabla["motivos_revision"] = pd.NA
    else:
        valores_sospechosos = valores_sospechosos.copy()
        valores_sospechosos["fecha"] = pd.to_datetime(
            valores_sospechosos["fecha"], errors="coerce"
        )
        motivos = (
            valores_sospechosos.groupby(claves, as_index=False)["motivos_revision"]
            .agg(_unicos_texto)
        )
        tabla = tabla.merge(motivos, on=claves, how="left", validate="one_to_one")

    claves_sensor = ["departamento", "codigoestacion", "codigosensor"]
    if sensores_cuarentena.empty:
        tabla["sensor_en_cuarentena"] = False
        tabla["motivo_cuarentena"] = pd.NA
    else:
        tabla = tabla.merge(
            sensores_cuarentena[claves_sensor + ["motivo_cuarentena"]],
            on=claves_sensor,
            how="left",
            validate="many_to_one",
        )
        tabla["sensor_en_cuarentena"] = tabla["motivo_cuarentena"].notna()

    observado = tabla["es_dia_observado"].astype("boolean").fillna(False)
    cobertura_evaluable = tabla["cobertura_evaluable"].astype("boolean").fillna(False)
    cobertura = tabla["cobertura_observada_pct"]
    estado = pd.Series("CANDIDATO_VALIDO", index=tabla.index, dtype="string")
    estado.loc[~observado] = "SIN_OBSERVACION"
    estado.loc[observado & ~cobertura_evaluable] = "COBERTURA_NO_EVALUABLE"
    estado.loc[
        observado & cobertura_evaluable & cobertura.lt(cobertura_minima_pct)
    ] = "COBERTURA_BAJA"
    estado.loc[
        observado & cobertura_evaluable & cobertura.gt(cobertura_maxima_pct)
    ] = "COBERTURA_EXCESIVA"
    estado.loc[observado & tabla["sensor_en_cuarentena"]] = "SENSOR_CUARENTENA"
    tabla["estado_candidato_sensor"] = estado
    tabla["es_candidato_valido"] = estado.eq("CANDIDATO_VALIDO")
    tabla["cobertura_superior_100"] = observado & cobertura.gt(100)
    tabla["requiere_revision"] = tabla["motivos_revision"].notna()
    tabla["cobertura_minima_regla_pct"] = float(cobertura_minima_pct)
    tabla["cobertura_maxima_regla_pct"] = float(cobertura_maxima_pct)
    return tabla


def _priorizar_sensor(
    candidatos: pd.DataFrame,
    prioridad_sensores: Sequence[str],
) -> pd.Series:
    prioridad = {str(sensor): posicion for posicion, sensor in enumerate(prioridad_sensores)}
    ordenados = candidatos.copy()
    ordenados["_prioridad"] = ordenados["codigosensor"].map(prioridad).fillna(
        len(prioridad)
    )
    ordenados = ordenados.sort_values(
        ["_prioridad", "cobertura_observada_pct", "codigosensor"],
        ascending=[True, False, True],
    )
    return ordenados.iloc[0]


def consolidar_estacion_dia(
    candidatos_sensor: pd.DataFrame,
    prioridad_sensores: Sequence[str] = ("0240", "0257"),
    tolerancia_sensores_mm: float = 0.1,
) -> pd.DataFrame:
    if tolerancia_sensores_mm < 0:
        raise ValueError("La tolerancia entre sensores no puede ser negativa.")

    filas = []
    for clave, grupo in candidatos_sensor.groupby(list(CLAVE_ESTACION_DIA), sort=True):
        departamento, codigoestacion, fecha = clave
        observados = grupo.loc[grupo["es_dia_observado"].fillna(False)]
        validos = grupo.loc[grupo["es_candidato_valido"]]
        sensores_observados = _unicos_texto(observados["codigosensor"])
        sensores_validos = _unicos_texto(validos["codigosensor"])
        sensores_cuarentena = _unicos_texto(
            grupo.loc[grupo["sensor_en_cuarentena"], "codigosensor"]
        )
        diferencia = (
            validos["precipitacion_observada_mm"].max()
            - validos["precipitacion_observada_mm"].min()
            if len(validos) > 1
            else 0.0 if len(validos) == 1 else pd.NA
        )

        seleccionado = None
        if validos.empty:
            if observados.empty:
                calidad = "SIN_OBSERVACION"
                motivo = "NINGUN_SENSOR_REPORTO"
            elif grupo["sensor_en_cuarentena"].any():
                calidad = "SIN_SENSOR_VALIDO"
                motivo = "SENSOR_EN_CUARENTENA"
            else:
                calidad = "SIN_SENSOR_VALIDO"
                motivo = "COBERTURA_FUERA_REGLA"
        elif (
            len(validos) > 1
            and float(diferencia) - tolerancia_sensores_mm > 1e-9
        ):
            calidad = "SENSORES_DISCREPANTES"
            motivo = "DIFERENCIA_SUPERA_TOLERANCIA"
        else:
            seleccionado = _priorizar_sensor(validos, prioridad_sensores)
            if len(validos) == 1:
                calidad = "VALIDO_SENSOR_UNICO"
                motivo = "UNICO_CANDIDATO_VALIDO"
            else:
                calidad = "VALIDO_SENSORES_CONCORDANTES"
                motivo = "SENSORES_DENTRO_TOLERANCIA"

        metadatos = observados if not observados.empty else grupo
        motivos_revision = _unicos_texto(observados["motivos_revision"])
        fila = {
            "variable": grupo["variable"].iloc[0],
            "dataset_id": grupo["dataset_id"].iloc[0],
            "departamento": departamento,
            "codigoestacion": codigoestacion,
            "fecha": fecha,
            "sensor_seleccionado": (
                seleccionado["codigosensor"] if seleccionado is not None else pd.NA
            ),
            "sensores_observados": sensores_observados,
            "sensores_validos": sensores_validos,
            "sensores_cuarentena": sensores_cuarentena,
            "numero_sensores_observados": len(observados),
            "numero_sensores_validos": len(validos),
            "precipitacion_observada_seleccionada_mm": (
                seleccionado["precipitacion_observada_mm"]
                if seleccionado is not None
                else pd.NA
            ),
            "precipitacion_diaria_mm": (
                seleccionado["precipitacion_observada_mm"]
                if seleccionado is not None
                else pd.NA
            ),
            "cobertura_sensor_seleccionado_pct": (
                seleccionado["cobertura_observada_pct"]
                if seleccionado is not None
                else pd.NA
            ),
            "diferencia_sensores_mm": diferencia,
            "es_dia_faltante": observados.empty,
            "calidad_dia": calidad,
            "motivo_calidad": motivo,
            "requiere_revision": bool(motivos_revision),
            "motivos_revision": motivos_revision,
            "municipios_observados": _unicos_texto(
                metadatos["municipios_observados"]
            ),
            "nombres_estacion_observados": _unicos_texto(
                metadatos["nombres_estacion_observados"]
            ),
            "latitud_mediana": (
                seleccionado["latitud_mediana"]
                if seleccionado is not None
                else _mediana_numerica(metadatos["latitud_mediana"])
            ),
            "longitud_mediana": (
                seleccionado["longitud_mediana"]
                if seleccionado is not None
                else _mediana_numerica(metadatos["longitud_mediana"])
            ),
            "regla_consolidacion": CONSOLIDATION_VERSION,
        }
        filas.append(fila)

    consolidado = pd.DataFrame(filas)
    if consolidado.empty:
        return consolidado
    consolidado["precipitacion_diaria_mm"] = consolidado[
        "precipitacion_diaria_mm"
    ].astype("Float64")
    consolidado["precipitacion_observada_seleccionada_mm"] = consolidado[
        "precipitacion_observada_seleccionada_mm"
    ].astype("Float64")
    if consolidado.duplicated(list(CLAVE_ESTACION_DIA)).any():
        raise RuntimeError("La consolidacion produjo llaves estacion-dia repetidas.")
    return consolidado.sort_values(list(CLAVE_ESTACION_DIA)).reset_index(drop=True)


def consolidar_precipitacion_diaria(
    calendario: pd.DataFrame,
    valores_sospechosos: pd.DataFrame,
    cobertura_minima_pct: float = 90.0,
    cobertura_maxima_pct: float = 102.0,
    tolerancia_sensores_mm: float = 0.1,
    prioridad_sensores: Sequence[str] = ("0240", "0257"),
    minimo_dias_cuarentena: int = 3,
) -> DailyConsolidationResult:
    calendario_validado = validar_calendario(calendario)
    cuarentena = identificar_sensores_cuarentena(
        valores_sospechosos,
        minimo_dias_persistentes=minimo_dias_cuarentena,
    )
    candidatos = clasificar_candidatos_sensor(
        calendario_validado,
        valores_sospechosos,
        cuarentena,
        cobertura_minima_pct=cobertura_minima_pct,
        cobertura_maxima_pct=cobertura_maxima_pct,
    )
    diario_estacion = consolidar_estacion_dia(
        candidatos,
        prioridad_sensores=prioridad_sensores,
        tolerancia_sensores_mm=tolerancia_sensores_mm,
    )
    metricas = {
        "regla_version": CONSOLIDATION_VERSION,
        "filas_calendario_entrada": len(calendario_validado),
        "filas_estacion_dia_salida": len(diario_estacion),
        "sensores_cuarentena": len(cuarentena),
        "dias_aceptados": int(diario_estacion["precipitacion_diaria_mm"].notna().sum()),
        "dias_sin_observacion": int(diario_estacion["es_dia_faltante"].sum()),
        "dias_sensores_discrepantes": int(
            diario_estacion["calidad_dia"].eq("SENSORES_DISCREPANTES").sum()
        ),
        "dias_sin_sensor_valido": int(
            diario_estacion["calidad_dia"].eq("SIN_SENSOR_VALIDO").sum()
        ),
        "cobertura_minima_pct": float(cobertura_minima_pct),
        "cobertura_maxima_pct": float(cobertura_maxima_pct),
        "tolerancia_sensores_mm": float(tolerancia_sensores_mm),
        "prioridad_sensores": list(prioridad_sensores),
        "minimo_dias_cuarentena": int(minimo_dias_cuarentena),
    }
    return DailyConsolidationResult(
        diario_estacion=diario_estacion,
        candidatos_sensor=candidatos,
        sensores_cuarentena=cuarentena,
        metricas=metricas,
    )
