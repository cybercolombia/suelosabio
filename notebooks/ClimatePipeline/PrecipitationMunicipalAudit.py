"""Auditoria de solo lectura para precipitacion diaria por municipio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd


AUDIT_VERSION = "auditoria_precipitacion_municipal_v1"
AGGREGATION_VERSION_ESPERADA = "precipitacion_municipio_dia_v1"
CLAVE_MUNICIPIO_DIA = ("codigo_municipio", "fecha")
COLUMNAS_REQUERIDAS = (
    "codigo_departamento",
    "departamento",
    "codigo_municipio",
    "municipio",
    "fecha",
    "estaciones_canonicas_total",
    "estaciones_esperadas",
    "estaciones_con_dato",
    "precipitacion_media_estaciones_mm",
    "precipitacion_mediana_estaciones_mm",
    "precipitacion_min_estaciones_mm",
    "precipitacion_max_estaciones_mm",
    "cobertura_estaciones_pct",
    "rango_estaciones_mm",
    "iqr_estaciones_mm",
    "calidad_municipio_dia",
    "es_valido_municipio_dia",
    "precipitacion_municipal_mm",
    "regla_agregacion",
)


@dataclass(slots=True)
class MunicipalAuditResult:
    cobertura_municipios: pd.DataFrame
    cobertura_periodos: pd.DataFrame
    cobertura_insuficiente: pd.DataFrame
    multiestacion_dias: pd.DataFrame
    resumen_multiestacion: pd.DataFrame
    sensibilidad_media_mediana_anual: pd.DataFrame
    sensibilidad_umbrales_lluvia: pd.DataFrame
    metricas: dict[str, Any]


def validar_clima_municipal(tabla: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(tabla.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas de clima municipal: {faltantes}.")

    diario = tabla.copy()
    diario["codigo_departamento"] = (
        diario["codigo_departamento"].astype("string").str.strip().str.zfill(2)
    )
    diario["codigo_municipio"] = (
        diario["codigo_municipio"].astype("string").str.strip().str.zfill(5)
    )
    diario["fecha"] = pd.to_datetime(diario["fecha"], errors="coerce")
    if diario["fecha"].isna().any():
        raise ValueError("El clima municipal contiene fechas invalidas.")
    if diario.duplicated(list(CLAVE_MUNICIPIO_DIA)).any():
        raise ValueError("El clima municipal contiene llaves municipio-dia repetidas.")
    if set(diario["regla_agregacion"].dropna().astype(str)) != {
        AGGREGATION_VERSION_ESPERADA
    }:
        raise ValueError("La auditoria recibio una version municipal inesperada.")

    diario["es_valido_municipio_dia"] = (
        diario["es_valido_municipio_dia"].astype("boolean").fillna(False)
    )
    for columna in (
        "estaciones_canonicas_total",
        "estaciones_esperadas",
        "estaciones_con_dato",
    ):
        diario[columna] = pd.to_numeric(diario[columna], errors="raise").astype(int)
        if diario[columna].lt(0).any():
            raise ValueError(f"Hay conteos negativos en {columna}.")

    if diario.loc[
        diario["es_valido_municipio_dia"], "precipitacion_municipal_mm"
    ].isna().any():
        raise ValueError("Existen filas validas sin precipitacion municipal.")
    if diario.loc[
        ~diario["es_valido_municipio_dia"], "precipitacion_municipal_mm"
    ].notna().any():
        raise ValueError("Existen filas no validas con precipitacion municipal.")
    if diario["precipitacion_municipal_mm"].dropna().lt(0).any():
        raise ValueError("La precipitacion municipal contiene valores negativos.")
    return diario.sort_values(["codigo_municipio", "fecha"]).reset_index(drop=True)


def _brecha_maxima(mascara: pd.Series) -> int:
    mascara = mascara.fillna(False).astype(bool).reset_index(drop=True)
    if not mascara.any():
        return 0
    grupos = mascara.ne(mascara.shift(fill_value=False)).cumsum()
    return int(mascara.groupby(grupos).sum().max())


def _clasificar_cobertura(
    estaciones: int,
    dias_esperados: int,
    dias_validos: int,
    cobertura_esperados_pct: float | None,
) -> str:
    if estaciones == 0:
        return "SIN_ESTACION_CANONICA"
    if dias_esperados == 0:
        return "SIN_VENTANA_ESPERADA"
    if dias_validos == 0:
        return "SIN_DIAS_VALIDOS"
    if cobertura_esperados_pct is None or pd.isna(cobertura_esperados_pct):
        return "NO_EVALUABLE"
    if cobertura_esperados_pct < 50:
        return "MENOR_50"
    if cobertura_esperados_pct < 70:
        return "50_A_69"
    if cobertura_esperados_pct < 80:
        return "70_A_79"
    if cobertura_esperados_pct < 90:
        return "80_A_89"
    return "90_O_MAS"


def resumir_cobertura_municipios(diario: pd.DataFrame) -> pd.DataFrame:
    filas = []
    claves = [
        "codigo_departamento",
        "departamento",
        "codigo_municipio",
        "municipio",
    ]
    for identificador, grupo in diario.groupby(claves, sort=True):
        esperada = grupo["estaciones_esperadas"].gt(0)
        valida = grupo["es_valido_municipio_dia"]
        dias_calendario = len(grupo)
        dias_esperados = int(esperada.sum())
        dias_validos = int(valida.sum())
        cobertura_calendario = 100.0 * dias_validos / dias_calendario
        cobertura_esperados = (
            100.0 * dias_validos / dias_esperados if dias_esperados else None
        )
        estaciones = int(grupo["estaciones_canonicas_total"].max())
        filas.append(
            {
                **dict(zip(claves, identificador)),
                "estaciones_canonicas_total": estaciones,
                "dias_calendario": dias_calendario,
                "dias_con_estacion_esperada": dias_esperados,
                "dias_validos": dias_validos,
                "dias_sin_datos_aceptados": int(
                    grupo["calidad_municipio_dia"].eq(
                        "SIN_DATOS_ACEPTADOS"
                    ).sum()
                ),
                "dias_cobertura_insuficiente": int(
                    grupo["calidad_municipio_dia"].eq(
                        "COBERTURA_INSUFICIENTE"
                    ).sum()
                ),
                "dias_validos_multiestacion": int(
                    grupo["calidad_municipio_dia"].eq(
                        "VALIDO_MULTIESTACION"
                    ).sum()
                ),
                "cobertura_sobre_calendario_pct": round(
                    cobertura_calendario, 2
                ),
                "cobertura_sobre_dias_esperados_pct": (
                    round(cobertura_esperados, 2)
                    if cobertura_esperados is not None
                    else pd.NA
                ),
                "brecha_maxima_sin_valor_dias": _brecha_maxima(~valida),
                "brecha_maxima_sin_valor_con_estacion_esperada_dias": (
                    _brecha_maxima(esperada & ~valida)
                ),
                "clasificacion_cobertura": _clasificar_cobertura(
                    estaciones,
                    dias_esperados,
                    dias_validos,
                    cobertura_esperados,
                ),
            }
        )
    return pd.DataFrame(filas).sort_values("codigo_municipio").reset_index(drop=True)


def _resumir_periodo(grupo: pd.DataFrame) -> pd.Series:
    esperada = grupo["estaciones_esperadas"].gt(0)
    valida = grupo["es_valido_municipio_dia"]
    dias_calendario = len(grupo)
    dias_esperados = int(esperada.sum())
    dias_validos = int(valida.sum())
    return pd.Series(
        {
            "dias_calendario": dias_calendario,
            "dias_con_estacion_esperada": dias_esperados,
            "dias_validos": dias_validos,
            "dias_sin_datos_aceptados": int(
                grupo["calidad_municipio_dia"].eq("SIN_DATOS_ACEPTADOS").sum()
            ),
            "dias_cobertura_insuficiente": int(
                grupo["calidad_municipio_dia"].eq(
                    "COBERTURA_INSUFICIENTE"
                ).sum()
            ),
            "cobertura_sobre_calendario_pct": round(
                100.0 * dias_validos / dias_calendario, 2
            ),
            "cobertura_sobre_dias_esperados_pct": (
                round(100.0 * dias_validos / dias_esperados, 2)
                if dias_esperados
                else pd.NA
            ),
            "brecha_maxima_sin_valor_dias": _brecha_maxima(~valida),
            "brecha_maxima_sin_valor_con_estacion_esperada_dias": (
                _brecha_maxima(esperada & ~valida)
            ),
        }
    )


def resumir_cobertura_periodos(diario: pd.DataFrame) -> pd.DataFrame:
    tabla = diario.copy()
    tabla["anio"] = tabla["fecha"].dt.year.astype(int)
    tabla["mes"] = tabla["fecha"].dt.month.astype(int)
    tabla["semestre"] = ((tabla["mes"] - 1) // 6 + 1).astype(int)
    identidad = [
        "codigo_departamento",
        "departamento",
        "codigo_municipio",
        "municipio",
    ]
    configuraciones = (
        ("MES", ["anio", "mes"]),
        ("SEMESTRE", ["anio", "semestre"]),
        ("ANIO", ["anio"]),
    )
    bloques = []
    for tipo, columnas_periodo in configuraciones:
        resumen = (
            tabla.groupby([*identidad, *columnas_periodo], sort=True)
            .apply(_resumir_periodo, include_groups=False)
            .reset_index()
        )
        resumen.insert(len(identidad), "tipo_periodo", tipo)
        if "mes" not in resumen:
            resumen["mes"] = pd.NA
        if "semestre" not in resumen:
            resumen["semestre"] = pd.NA
        bloques.append(resumen)
    return pd.concat(bloques, ignore_index=True).sort_values(
        ["codigo_municipio", "anio", "tipo_periodo", "semestre", "mes"],
        na_position="last",
    ).reset_index(drop=True)


def auditar_multiestacion(
    diario: pd.DataFrame,
    umbrales_lluvia_mm: Iterable[float],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    multi = diario.loc[
        diario["calidad_municipio_dia"].eq("VALIDO_MULTIESTACION")
    ].copy()
    multi["diferencia_media_mediana_mm"] = (
        multi["precipitacion_media_estaciones_mm"]
        - multi["precipitacion_mediana_estaciones_mm"]
    )
    multi["diferencia_absoluta_media_mediana_mm"] = multi[
        "diferencia_media_mediana_mm"
    ].abs()
    denominador = multi["precipitacion_mediana_estaciones_mm"].abs()
    multi["diferencia_pct_sobre_mediana"] = (
        100.0 * multi["diferencia_absoluta_media_mediana_mm"] / denominador
    ).where(denominador.gt(0))

    claves_municipio = [
        "codigo_departamento",
        "departamento",
        "codigo_municipio",
        "municipio",
    ]
    if multi.empty:
        resumen = pd.DataFrame()
    else:
        resumen = (
            multi.groupby(claves_municipio, as_index=False)
            .agg(
                dias_multiestacion=("fecha", "size"),
                estaciones_con_dato_max=("estaciones_con_dato", "max"),
                diferencia_absoluta_media_mediana_mediana_mm=(
                    "diferencia_absoluta_media_mediana_mm",
                    "median",
                ),
                diferencia_absoluta_media_mediana_p95_mm=(
                    "diferencia_absoluta_media_mediana_mm",
                    lambda serie: serie.quantile(0.95),
                ),
                diferencia_absoluta_media_mediana_max_mm=(
                    "diferencia_absoluta_media_mediana_mm",
                    "max",
                ),
                rango_estaciones_mediana_mm=("rango_estaciones_mm", "median"),
                rango_estaciones_p95_mm=(
                    "rango_estaciones_mm",
                    lambda serie: serie.quantile(0.95),
                ),
                rango_estaciones_max_mm=("rango_estaciones_mm", "max"),
                iqr_estaciones_p95_mm=(
                    "iqr_estaciones_mm",
                    lambda serie: serie.quantile(0.95),
                ),
            )
            .sort_values(
                "diferencia_absoluta_media_mediana_p95_mm",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    sensibilidad_umbral = []
    for umbral in sorted({float(valor) for valor in umbrales_lluvia_mm}):
        if umbral < 0:
            raise ValueError("Los umbrales de lluvia no pueden ser negativos.")
        media_lluvia = multi["precipitacion_media_estaciones_mm"].ge(umbral)
        mediana_lluvia = multi["precipitacion_mediana_estaciones_mm"].ge(umbral)
        diferentes = media_lluvia.ne(mediana_lluvia)
        sensibilidad_umbral.append(
            {
                "umbral_lluvia_mm": umbral,
                "dias_multiestacion_evaluados": len(multi),
                "dias_clasificacion_diferente": int(diferentes.sum()),
                "porcentaje_clasificacion_diferente": round(
                    100.0 * diferentes.mean() if len(multi) else 0.0,
                    4,
                ),
            }
        )

    validos = diario.loc[diario["es_valido_municipio_dia"]].copy()
    validos["anio"] = validos["fecha"].dt.year.astype(int)
    sensibilidad_anual = (
        validos.groupby([*claves_municipio, "anio"], as_index=False)
        .agg(
            dias_validos=("fecha", "size"),
            dias_multiestacion=(
                "calidad_municipio_dia",
                lambda serie: int(serie.eq("VALIDO_MULTIESTACION").sum()),
            ),
            suma_mediana_dias_validos_mm=(
                "precipitacion_mediana_estaciones_mm",
                "sum",
            ),
            suma_media_dias_validos_mm=(
                "precipitacion_media_estaciones_mm",
                "sum",
            ),
        )
    )
    sensibilidad_anual["diferencia_suma_media_mediana_mm"] = (
        sensibilidad_anual["suma_media_dias_validos_mm"]
        - sensibilidad_anual["suma_mediana_dias_validos_mm"]
    )
    denominador_anual = sensibilidad_anual["suma_mediana_dias_validos_mm"].abs()
    sensibilidad_anual["diferencia_suma_pct_sobre_mediana"] = (
        100.0
        * sensibilidad_anual["diferencia_suma_media_mediana_mm"].abs()
        / denominador_anual
    ).where(denominador_anual.gt(0))
    return (
        multi.sort_values(
            ["diferencia_absoluta_media_mediana_mm", "rango_estaciones_mm"],
            ascending=False,
        ).reset_index(drop=True),
        resumen,
        sensibilidad_anual.sort_values(
            "diferencia_suma_pct_sobre_mediana",
            ascending=False,
            na_position="last",
        ).reset_index(drop=True),
        pd.DataFrame(sensibilidad_umbral),
    )


def auditar_precipitacion_municipal(
    tabla: pd.DataFrame,
    umbrales_lluvia_mm: Iterable[float] = (0.1, 1.0, 5.0, 10.0, 20.0),
) -> MunicipalAuditResult:
    diario = validar_clima_municipal(tabla)
    cobertura_municipios = resumir_cobertura_municipios(diario)
    cobertura_periodos = resumir_cobertura_periodos(diario)
    insuficiente = diario.loc[
        diario["calidad_municipio_dia"].eq("COBERTURA_INSUFICIENTE")
    ].copy()
    (
        multi,
        resumen_multi,
        sensibilidad_anual,
        sensibilidad_umbrales,
    ) = auditar_multiestacion(diario, umbrales_lluvia_mm)

    dias_esperados = int(diario["estaciones_esperadas"].gt(0).sum())
    dias_validos = int(diario["es_valido_municipio_dia"].sum())
    diferencia_multi = multi["diferencia_absoluta_media_mediana_mm"]
    metricas = {
        "audit_version": AUDIT_VERSION,
        "estado": "COMPLETA_CON_REVISION_PENDIENTE",
        "filas_municipio_dia": len(diario),
        "municipios": int(diario["codigo_municipio"].nunique()),
        "municipios_con_estacion_canonica": int(
            cobertura_municipios["estaciones_canonicas_total"].gt(0).sum()
        ),
        "municipios_sin_estacion_canonica": int(
            cobertura_municipios["estaciones_canonicas_total"].eq(0).sum()
        ),
        "dias_con_estacion_esperada": dias_esperados,
        "dias_validos": dias_validos,
        "cobertura_agregada_sobre_dias_esperados_pct": round(
            100.0 * dias_validos / dias_esperados if dias_esperados else 0.0,
            2,
        ),
        "dias_cobertura_insuficiente": len(insuficiente),
        "dias_validos_multiestacion": len(multi),
        "municipios_con_dias_multiestacion": int(
            multi["codigo_municipio"].nunique()
        ),
        "diferencia_absoluta_media_mediana_p50_mm": (
            float(diferencia_multi.quantile(0.50)) if len(multi) else None
        ),
        "diferencia_absoluta_media_mediana_p95_mm": (
            float(diferencia_multi.quantile(0.95)) if len(multi) else None
        ),
        "diferencia_absoluta_media_mediana_max_mm": (
            float(diferencia_multi.max()) if len(multi) else None
        ),
    }
    return MunicipalAuditResult(
        cobertura_municipios=cobertura_municipios,
        cobertura_periodos=cobertura_periodos,
        cobertura_insuficiente=insuficiente.reset_index(drop=True),
        multiestacion_dias=multi,
        resumen_multiestacion=resumen_multi,
        sensibilidad_media_mediana_anual=sensibilidad_anual,
        sensibilidad_umbrales_lluvia=sensibilidad_umbrales,
        metricas=metricas,
    )
