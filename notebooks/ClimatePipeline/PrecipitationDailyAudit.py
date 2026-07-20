"""Auditoria de solo lectura para la capa diaria preliminar de precipitacion."""

from __future__ import annotations

import calendar as month_calendar
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import pandas as pd


AUDIT_VERSION = "auditoria_precipitacion_diaria_v1"
CLAVE_DIARIA = ("departamento", "codigoestacion", "codigosensor", "fecha")
COLUMNAS_REQUERIDAS = (
    "variable",
    "dataset_id",
    "departamento",
    "codigoestacion",
    "codigosensor",
    "fecha",
    "precipitacion_observada_mm",
    "observaciones_validas",
    "observaciones_positivas",
    "valor_intervalo_max_mm",
    "municipios_observados",
    "nombres_estacion_observados",
    "intervalo_moda_segundos",
    "observaciones_esperadas",
    "cobertura_observada_pct",
    "cobertura_evaluable",
    "precipitacion_diaria_mm",
    "calidad_dia",
    "regla_version",
)


@dataclass(slots=True)
class DailyAuditResult:
    calendario: pd.DataFrame
    resumen_particiones: pd.DataFrame
    resumen_pares: pd.DataFrame
    valores_sospechosos: pd.DataFrame
    comparaciones_sensores: pd.DataFrame
    resumen_sensores_paralelos: pd.DataFrame
    metricas: dict[str, Any]


def validar_capa_diaria(diario: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(diario.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas de la capa diaria: {faltantes}.")

    tabla = diario.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    if tabla["fecha"].isna().any():
        raise ValueError("La capa diaria contiene fechas no interpretables.")
    if tabla.duplicated(list(CLAVE_DIARIA)).any():
        raise ValueError("La capa diaria contiene llaves estacion-sensor-fecha repetidas.")
    if tabla["precipitacion_observada_mm"].lt(0).any():
        raise ValueError("La capa diaria contiene precipitacion observada negativa.")
    if tabla["observaciones_validas"].lt(0).any():
        raise ValueError("La capa diaria contiene conteos de observaciones negativos.")

    tabla["anio"] = tabla["fecha"].dt.year.astype(int)
    tabla["mes"] = tabla["fecha"].dt.month.astype(int)
    return tabla


def _estado_cobertura(fila: pd.Series, umbral_cobertura_pct: float) -> str:
    if not fila["es_dia_observado"]:
        return "SIN_OBSERVACION"
    if not bool(fila.get("cobertura_evaluable", False)):
        return "NO_EVALUABLE"
    cobertura = fila.get("cobertura_observada_pct")
    if pd.isna(cobertura):
        return "NO_EVALUABLE"
    if cobertura > 100:
        return "MAYOR_100_REVISAR"
    if cobertura < umbral_cobertura_pct:
        return "COBERTURA_BAJA"
    return "COBERTURA_CANDIDATA_SUFICIENTE"


def construir_calendario(
    diario: pd.DataFrame,
    umbral_cobertura_pct: float = 90.0,
) -> pd.DataFrame:
    if not 0 < umbral_cobertura_pct <= 100:
        raise ValueError("El umbral de cobertura debe estar entre 0 y 100.")

    bloques = []
    claves_particion = ["variable", "dataset_id", "departamento", "anio", "mes"]
    for particion, grupo in diario.groupby(claves_particion, sort=True):
        variable, dataset_id, departamento, anio, mes = particion
        fin_mes = month_calendar.monthrange(int(anio), int(mes))[1]
        fechas = pd.date_range(
            f"{int(anio):04d}-{int(mes):02d}-01",
            periods=fin_mes,
            freq="D",
        )
        pares = grupo[["codigoestacion", "codigosensor"]].drop_duplicates()
        pares["_union"] = 1
        calendario = pd.DataFrame({"fecha": fechas, "_union": 1})
        bloque = pares.merge(calendario, on="_union", how="inner").drop(
            columns="_union"
        )
        bloque.insert(0, "variable", variable)
        bloque.insert(1, "dataset_id", dataset_id)
        bloque.insert(2, "departamento", departamento)
        bloque["anio"] = int(anio)
        bloque["mes"] = int(mes)
        bloques.append(bloque)

    if not bloques:
        return pd.DataFrame()

    calendario = pd.concat(bloques, ignore_index=True)
    columnas_union = list(CLAVE_DIARIA)
    columnas_diarias = [
        columna
        for columna in diario.columns
        if columna not in {"variable", "dataset_id", "anio", "mes"}
        and columna not in columnas_union
    ]
    calendario = calendario.merge(
        diario[columnas_union + columnas_diarias],
        on=columnas_union,
        how="left",
        validate="one_to_one",
    )
    calendario["es_dia_observado"] = calendario["observaciones_validas"].notna()
    calendario["es_dia_ausente"] = ~calendario["es_dia_observado"]
    calendario["fecha_observada"] = calendario["fecha"].where(
        calendario["es_dia_observado"]
    )
    calendario["estado_cobertura_candidato"] = calendario.apply(
        _estado_cobertura,
        axis=1,
        umbral_cobertura_pct=umbral_cobertura_pct,
    )
    calendario["umbral_cobertura_candidato_pct"] = float(umbral_cobertura_pct)
    return calendario.sort_values(list(CLAVE_DIARIA)).reset_index(drop=True)


def resumir_particiones(
    calendario: pd.DataFrame,
    diario: pd.DataFrame,
) -> pd.DataFrame:
    claves = ["variable", "dataset_id", "departamento", "anio", "mes"]
    filas = []
    for particion, calendario_mes in calendario.groupby(claves, sort=True):
        mascara = pd.Series(True, index=diario.index)
        for columna, valor in zip(claves, particion):
            mascara &= diario[columna].eq(valor)
        observado = diario.loc[mascara]
        dias_presentes = observado["fecha"].dt.normalize().nunique()
        dias_mes = month_calendar.monthrange(int(particion[3]), int(particion[4]))[1]
        cobertura = observado["cobertura_observada_pct"]
        filas.append(
            {
                **dict(zip(claves, particion)),
                "dias_calendario": dias_mes,
                "dias_con_algun_registro": int(dias_presentes),
                "dias_sin_ningun_registro": int(dias_mes - dias_presentes),
                "pares_estacion_sensor": int(
                    observado[["codigoestacion", "codigosensor"]]
                    .drop_duplicates()
                    .shape[0]
                ),
                "filas_calendario": len(calendario_mes),
                "filas_observadas": len(observado),
                "filas_ausentes": int(calendario_mes["es_dia_ausente"].sum()),
                "cobertura_mediana_pct": cobertura.median(),
                "dias_cobertura_mayor_100": int(cobertura.gt(100).sum()),
                "dias_cobertura_baja": int(
                    calendario_mes["estado_cobertura_candidato"]
                    .eq("COBERTURA_BAJA")
                    .sum()
                ),
                "precipitacion_observada_max_mm": observado[
                    "precipitacion_observada_mm"
                ].max(),
            }
        )
    return pd.DataFrame(filas)


def resumir_pares(calendario: pd.DataFrame) -> pd.DataFrame:
    claves = [
        "variable",
        "dataset_id",
        "departamento",
        "anio",
        "mes",
        "codigoestacion",
        "codigosensor",
    ]
    return (
        calendario.groupby(claves, as_index=False, dropna=False)
        .agg(
            dias_calendario=("fecha", "size"),
            dias_observados=("es_dia_observado", "sum"),
            dias_ausentes=("es_dia_ausente", "sum"),
            primera_fecha_observada=("fecha_observada", "min"),
            ultima_fecha_observada=("fecha_observada", "max"),
            dias_cobertura_baja=(
                "estado_cobertura_candidato",
                lambda s: int(s.eq("COBERTURA_BAJA").sum()),
            ),
            dias_cobertura_mayor_100=(
                "estado_cobertura_candidato",
                lambda s: int(s.eq("MAYOR_100_REVISAR").sum()),
            ),
            cobertura_mediana_pct=("cobertura_observada_pct", "median"),
            precipitacion_observada_max_mm=("precipitacion_observada_mm", "max"),
            municipios_observados=(
                "municipios_observados",
                lambda s: " | ".join(sorted(set(s.dropna().astype(str)))),
            ),
        )
    )


def detectar_valores_sospechosos(
    diario: pd.DataFrame,
    umbral_total_extremo_mm: float = 200.0,
    umbral_intervalo_sospechoso_mm: float = 25.0,
    proporcion_positivos_sospechosa: float = 0.8,
    umbral_total_patron_positivo_mm: float = 100.0,
) -> pd.DataFrame:
    tabla = diario.copy()
    tabla["proporcion_observaciones_positivas"] = (
        tabla["observaciones_positivas"] / tabla["observaciones_validas"]
    )
    tabla["promedio_intervalo_positivo_mm"] = (
        tabla["precipitacion_observada_mm"]
        / tabla["observaciones_positivas"].replace(0, pd.NA)
    )
    tabla["p99_positivo_particion_mm"] = tabla.groupby(
        ["departamento", "anio", "mes"]
    )["precipitacion_observada_mm"].transform(
        lambda s: s.loc[s > 0].quantile(0.99) if s.gt(0).any() else pd.NA
    )

    motivos = pd.Series("", index=tabla.index, dtype="string")

    def agregar(mascara: pd.Series, motivo: str) -> None:
        separador = motivos.ne("") & mascara
        motivos.loc[separador] += "|"
        motivos.loc[mascara] += motivo

    agregar(
        tabla["precipitacion_observada_mm"].ge(umbral_total_extremo_mm),
        "TOTAL_DIARIO_MUY_ALTO",
    )
    agregar(
        tabla["valor_intervalo_max_mm"].ge(umbral_intervalo_sospechoso_mm),
        "INTERVALO_MUY_ALTO",
    )
    agregar(
        tabla["proporcion_observaciones_positivas"].ge(
            proporcion_positivos_sospechosa
        )
        & tabla["precipitacion_observada_mm"].ge(umbral_total_patron_positivo_mm),
        "POSITIVOS_PERSISTENTES",
    )
    agregar(
        tabla["precipitacion_observada_mm"].gt(0)
        & tabla["precipitacion_observada_mm"].ge(
            tabla["p99_positivo_particion_mm"]
        ),
        "EXTREMO_P99_PARTICION",
    )
    agregar(
        tabla["cobertura_observada_pct"].gt(100),
        "COBERTURA_MAYOR_100",
    )
    tabla["motivos_revision"] = motivos
    return tabla.loc[motivos.ne("")].sort_values(
        ["departamento", "anio", "mes", "precipitacion_observada_mm"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)


def comparar_sensores_paralelos(
    diario: pd.DataFrame,
    tolerancia_mm: float = 0.1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    comparaciones = []
    claves_grupo = ["variable", "dataset_id", "departamento", "codigoestacion"]
    for grupo_id, grupo in diario.groupby(claves_grupo, sort=True):
        sensores = sorted(grupo["codigosensor"].dropna().unique())
        for sensor_a, sensor_b in combinations(sensores, 2):
            columnas = [
                "fecha",
                "precipitacion_observada_mm",
                "cobertura_observada_pct",
            ]
            izquierda = grupo.loc[grupo["codigosensor"].eq(sensor_a), columnas]
            derecha = grupo.loc[grupo["codigosensor"].eq(sensor_b), columnas]
            comparacion = izquierda.merge(
                derecha,
                on="fecha",
                how="outer",
                suffixes=("_a", "_b"),
                validate="one_to_one",
            )
            comparacion.insert(0, "sensor_b", sensor_b)
            comparacion.insert(0, "sensor_a", sensor_a)
            for posicion, (columna, valor) in enumerate(
                zip(claves_grupo, grupo_id)
            ):
                comparacion.insert(posicion, columna, valor)
            comparacion["ambos_observados"] = comparacion[
                ["precipitacion_observada_mm_a", "precipitacion_observada_mm_b"]
            ].notna().all(axis=1)
            comparacion["diferencia_abs_mm"] = (
                comparacion["precipitacion_observada_mm_a"]
                - comparacion["precipitacion_observada_mm_b"]
            ).abs()
            comparacion["concuerdan_tolerancia"] = (
                comparacion["ambos_observados"]
                & comparacion["diferencia_abs_mm"].le(tolerancia_mm)
            )
            comparacion["uno_cero_otro_positivo"] = comparacion[
                "ambos_observados"
            ] & (
                comparacion["precipitacion_observada_mm_a"].eq(0)
                ^ comparacion["precipitacion_observada_mm_b"].eq(0)
            )
            comparaciones.append(comparacion)

    columnas_resumen = claves_grupo + [
        "sensor_a",
        "sensor_b",
        "dias_union",
        "dias_ambos_observados",
        "dias_solo_un_sensor",
        "dias_concuerdan_tolerancia",
        "dias_uno_cero_otro_positivo",
        "diferencia_abs_mediana_mm",
        "diferencia_abs_max_mm",
        "correlacion",
    ]
    columnas_detalle = claves_grupo + [
        "sensor_a",
        "sensor_b",
        "fecha",
        "precipitacion_observada_mm_a",
        "cobertura_observada_pct_a",
        "precipitacion_observada_mm_b",
        "cobertura_observada_pct_b",
        "ambos_observados",
        "diferencia_abs_mm",
        "concuerdan_tolerancia",
        "uno_cero_otro_positivo",
    ]
    if not comparaciones:
        return (
            pd.DataFrame(columns=columnas_detalle),
            pd.DataFrame(columns=columnas_resumen),
        )

    detalle = pd.concat(comparaciones, ignore_index=True)
    filas_resumen = []
    claves_par = claves_grupo + ["sensor_a", "sensor_b"]
    for identificador, grupo in detalle.groupby(claves_par, sort=True):
        solapados = grupo.loc[grupo["ambos_observados"]]
        correlacion = pd.NA
        if (
            len(solapados) >= 2
            and solapados["precipitacion_observada_mm_a"].nunique() > 1
            and solapados["precipitacion_observada_mm_b"].nunique() > 1
        ):
            correlacion = solapados[
                ["precipitacion_observada_mm_a", "precipitacion_observada_mm_b"]
            ].corr().iloc[0, 1]
        filas_resumen.append(
            {
                **dict(zip(claves_par, identificador)),
                "dias_union": len(grupo),
                "dias_ambos_observados": int(grupo["ambos_observados"].sum()),
                "dias_solo_un_sensor": int((~grupo["ambos_observados"]).sum()),
                "dias_concuerdan_tolerancia": int(
                    grupo["concuerdan_tolerancia"].sum()
                ),
                "dias_uno_cero_otro_positivo": int(
                    grupo["uno_cero_otro_positivo"].sum()
                ),
                "diferencia_abs_mediana_mm": grupo["diferencia_abs_mm"].median(),
                "diferencia_abs_max_mm": grupo["diferencia_abs_mm"].max(),
                "correlacion": correlacion,
            }
        )
    return detalle, pd.DataFrame(filas_resumen, columns=columnas_resumen)


def auditar_precipitacion_diaria(
    diario: pd.DataFrame,
    umbral_cobertura_pct: float = 90.0,
    umbral_total_extremo_mm: float = 200.0,
    umbral_intervalo_sospechoso_mm: float = 25.0,
    tolerancia_sensores_mm: float = 0.1,
) -> DailyAuditResult:
    validado = validar_capa_diaria(diario)
    calendario = construir_calendario(validado, umbral_cobertura_pct)
    resumen_particiones = resumir_particiones(calendario, validado)
    resumen_pares = resumir_pares(calendario)
    sospechosos = detectar_valores_sospechosos(
        validado,
        umbral_total_extremo_mm=umbral_total_extremo_mm,
        umbral_intervalo_sospechoso_mm=umbral_intervalo_sospechoso_mm,
    )
    comparaciones, resumen_paralelos = comparar_sensores_paralelos(
        validado,
        tolerancia_mm=tolerancia_sensores_mm,
    )
    metricas = {
        "audit_version": AUDIT_VERSION,
        "filas_diarias_entrada": len(validado),
        "filas_calendario": len(calendario),
        "dias_ausentes_estacion_sensor": int(calendario["es_dia_ausente"].sum()),
        "filas_revision": len(sospechosos),
        "pares_sensores_paralelos": len(resumen_paralelos),
        "umbral_cobertura_candidato_pct": float(umbral_cobertura_pct),
        "umbral_total_extremo_mm": float(umbral_total_extremo_mm),
        "umbral_intervalo_sospechoso_mm": float(
            umbral_intervalo_sospechoso_mm
        ),
        "tolerancia_sensores_mm": float(tolerancia_sensores_mm),
    }
    return DailyAuditResult(
        calendario=calendario,
        resumen_particiones=resumen_particiones,
        resumen_pares=resumen_pares,
        valores_sospechosos=sospechosos,
        comparaciones_sensores=comparaciones,
        resumen_sensores_paralelos=resumen_paralelos,
        metricas=metricas,
    )
