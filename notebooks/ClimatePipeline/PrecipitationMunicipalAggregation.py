"""Agregacion trazable de precipitacion de estacion-dia a municipio-dia."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


AGGREGATION_VERSION = "precipitacion_municipio_dia_v1"
DEPARTAMENTOS_OBJETIVO = {"15", "25"}
CLAVE_ESTACION_DIA = ("departamento", "codigoestacion", "fecha")
CLAVE_MUNICIPIO_DIA = ("codigo_municipio", "fecha")
COLUMNAS_DIARIO_REQUERIDAS = (
    "variable",
    "dataset_id",
    "departamento",
    "codigoestacion",
    "fecha",
    "precipitacion_diaria_mm",
    "calidad_dia",
    "requiere_revision",
)
COLUMNAS_GEOGRAFIA_REQUERIDAS = (
    "codigoestacion",
    "fecha_inicio_clima",
    "fecha_fin_clima",
    "asignacion_canonica",
    "codigo_municipio_canonico",
    "municipio_canonico",
)
COLUMNAS_DIVIPOLA_REQUERIDAS = (
    "codigo_departamento",
    "codigo_municipio",
    "Nombre Departamento",
    "Nombre Municipio",
)


@dataclass(slots=True)
class MunicipalAggregationResult:
    diario_municipal: pd.DataFrame
    resumen_municipio: pd.DataFrame
    metricas: dict[str, Any]


def _unir_codigos(serie: pd.Series) -> str:
    return " | ".join(sorted(set(serie.dropna().astype(str))))


def validar_diario_estacion(diario: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_DIARIO_REQUERIDAS) - set(diario.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del clima estacion-dia: {faltantes}.")

    tabla = diario.copy()
    tabla["codigoestacion"] = tabla["codigoestacion"].astype("string").str.strip()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    tabla["precipitacion_diaria_mm"] = pd.to_numeric(
        tabla["precipitacion_diaria_mm"],
        errors="coerce",
    ).astype("Float64")
    if tabla["codigoestacion"].isna().any() or tabla["codigoestacion"].eq("").any():
        raise ValueError("El clima estacion-dia contiene codigos vacios.")
    if tabla["fecha"].isna().any():
        raise ValueError("El clima estacion-dia contiene fechas invalidas.")
    if tabla.duplicated(list(CLAVE_ESTACION_DIA)).any():
        raise ValueError("El clima contiene llaves estacion-dia repetidas.")
    if tabla.duplicated(["codigoestacion", "fecha"]).any():
        raise ValueError(
            "Una estacion aparece el mismo dia bajo mas de un departamento."
        )
    if tabla["precipitacion_diaria_mm"].dropna().lt(0).any():
        raise ValueError("La precipitacion estacion-dia contiene valores negativos.")
    if set(tabla["variable"].dropna().astype(str)) != {"precipitacion"}:
        raise ValueError("El contrato municipal solo acepta precipitacion.")
    tabla["requiere_revision"] = (
        tabla["requiere_revision"].astype("boolean").fillna(False)
    )
    return tabla


def validar_estaciones_canonicas(estaciones: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_GEOGRAFIA_REQUERIDAS) - set(estaciones.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas de geografia canonica: {faltantes}.")

    tabla = estaciones.copy()
    tabla["codigoestacion"] = tabla["codigoestacion"].astype("string").str.strip()
    tabla["codigo_municipio_canonico"] = (
        tabla["codigo_municipio_canonico"].astype("string").str.strip().str.zfill(5)
    )
    for columna in ("fecha_inicio_clima", "fecha_fin_clima"):
        tabla[columna] = pd.to_datetime(tabla[columna], errors="coerce")

    if tabla["codigoestacion"].duplicated().any():
        raise ValueError("La geografia canonica contiene estaciones repetidas.")
    if not tabla["asignacion_canonica"].astype("boolean").fillna(False).all():
        raise ValueError("La entrada geografica contiene asignaciones no canonicas.")
    if tabla[["fecha_inicio_clima", "fecha_fin_clima"]].isna().any().any():
        raise ValueError("La geografia canonica contiene ventanas temporales invalidas.")
    if tabla["fecha_inicio_clima"].gt(tabla["fecha_fin_clima"]).any():
        raise ValueError("Una estacion inicia despues de su fecha final.")
    if not tabla["codigo_municipio_canonico"].str.fullmatch(r"\d{5}").all():
        raise ValueError("La geografia contiene codigos municipales invalidos.")
    if not tabla["codigo_municipio_canonico"].str[:2].isin(
        DEPARTAMENTOS_OBJETIVO
    ).all():
        raise ValueError("La geografia canonica contiene municipios fuera del alcance.")
    return tabla


def validar_divipola_objetivo(divipola: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_DIVIPOLA_REQUERIDAS) - set(divipola.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas DIVIPOLA: {faltantes}.")

    tabla = divipola.copy()
    tabla["codigo_departamento"] = (
        tabla["codigo_departamento"].astype("string").str.strip().str.zfill(2)
    )
    tabla["codigo_municipio"] = (
        tabla["codigo_municipio"].astype("string").str.strip().str.zfill(5)
    )
    tabla = tabla.loc[
        tabla["codigo_departamento"].isin(DEPARTAMENTOS_OBJETIVO)
    ].copy()
    if tabla["codigo_municipio"].duplicated().any():
        raise ValueError("DIVIPOLA contiene municipios objetivo repetidos.")
    if not tabla["codigo_municipio"].str.fullmatch(r"\d{5}").all():
        raise ValueError("DIVIPOLA contiene codigos municipales invalidos.")
    return tabla


def _expandir_estaciones_esperadas(
    estaciones: pd.DataFrame,
    fecha_inicio: pd.Timestamp,
    fecha_fin: pd.Timestamp,
) -> pd.DataFrame:
    fragmentos = []
    for fila in estaciones.itertuples(index=False):
        inicio = max(pd.Timestamp(fila.fecha_inicio_clima), fecha_inicio)
        fin = min(pd.Timestamp(fila.fecha_fin_clima), fecha_fin)
        if inicio > fin:
            continue
        fragmentos.append(
            pd.DataFrame(
                {
                    "codigo_municipio": fila.codigo_municipio_canonico,
                    "fecha": pd.date_range(inicio, fin, freq="D"),
                    "codigoestacion": fila.codigoestacion,
                }
            )
        )
    if not fragmentos:
        return pd.DataFrame(
            columns=["codigo_municipio", "fecha", "codigoestacion"]
        )
    return pd.concat(fragmentos, ignore_index=True)


def _resumir_aportes_estacion(diario: pd.DataFrame) -> pd.DataFrame:
    claves = ["codigo_municipio", "fecha"]
    filas = (
        diario.groupby(claves, as_index=False)
        .agg(
            estaciones_con_fila=("codigoestacion", "nunique"),
            estaciones_con_fila_codigos=("codigoestacion", _unir_codigos),
            estaciones_con_dato=(
                "precipitacion_diaria_mm",
                "count",
            ),
            aportes_estacion_requieren_revision=("requiere_revision", "sum"),
        )
    )
    aceptados = diario.loc[diario["precipitacion_diaria_mm"].notna()].copy()
    if aceptados.empty:
        return filas

    estadisticas = (
        aceptados.groupby(claves, as_index=False)
        .agg(
            estaciones_con_dato_codigos=("codigoestacion", _unir_codigos),
            precipitacion_media_estaciones_mm=("precipitacion_diaria_mm", "mean"),
            precipitacion_mediana_estaciones_mm=(
                "precipitacion_diaria_mm",
                "median",
            ),
            precipitacion_min_estaciones_mm=("precipitacion_diaria_mm", "min"),
            precipitacion_max_estaciones_mm=("precipitacion_diaria_mm", "max"),
            precipitacion_std_estaciones_mm=("precipitacion_diaria_mm", "std"),
        )
    )
    cuantiles = (
        aceptados.groupby(claves)["precipitacion_diaria_mm"]
        .quantile([0.25, 0.75])
        .unstack()
        .rename(
            columns={
                0.25: "precipitacion_q25_estaciones_mm",
                0.75: "precipitacion_q75_estaciones_mm",
            }
        )
        .reset_index()
    )
    estadisticas = estadisticas.merge(
        cuantiles,
        on=claves,
        how="left",
        validate="one_to_one",
    )
    return filas.merge(estadisticas, on=claves, how="left", validate="one_to_one")


def agregar_precipitacion_municipal(
    diario_estacion: pd.DataFrame,
    estaciones_canonicas: pd.DataFrame,
    divipola: pd.DataFrame,
    fecha_inicio: str | pd.Timestamp,
    fecha_fin: str | pd.Timestamp,
    cobertura_minima_pct: float = 50.0,
) -> MunicipalAggregationResult:
    if not 0 < cobertura_minima_pct <= 100:
        raise ValueError("La cobertura minima debe estar entre 0 y 100.")
    inicio = pd.Timestamp(fecha_inicio)
    fin = pd.Timestamp(fecha_fin)
    if pd.isna(inicio) or pd.isna(fin) or inicio > fin:
        raise ValueError("El intervalo temporal de agregacion es invalido.")

    diario = validar_diario_estacion(diario_estacion)
    estaciones = validar_estaciones_canonicas(estaciones_canonicas)
    municipios = validar_divipola_objetivo(divipola)
    diario = diario.loc[diario["fecha"].between(inicio, fin)].copy()

    estaciones_diario = set(diario["codigoestacion"].astype(str))
    estaciones_geo = set(estaciones["codigoestacion"].astype(str))
    estaciones_relevantes = set(
        estaciones.loc[
            estaciones["fecha_inicio_clima"].le(fin)
            & estaciones["fecha_fin_clima"].ge(inicio),
            "codigoestacion",
        ].astype(str)
    )
    faltantes = sorted(estaciones_relevantes - estaciones_diario)
    if faltantes:
        raise ValueError(
            "Hay estaciones canonicas sin historia diaria en el intervalo: "
            f"{faltantes[:10]}."
        )

    red_estatica = (
        estaciones.groupby("codigo_municipio_canonico", as_index=False)
        .agg(
            estaciones_canonicas_total=("codigoestacion", "nunique"),
            estaciones_canonicas_codigos=("codigoestacion", _unir_codigos),
        )
        .rename(columns={"codigo_municipio_canonico": "codigo_municipio"})
    )
    esperadas_larga = _expandir_estaciones_esperadas(estaciones, inicio, fin)
    esperadas = (
        esperadas_larga.groupby(["codigo_municipio", "fecha"], as_index=False)
        .agg(
            estaciones_esperadas=("codigoestacion", "nunique"),
            estaciones_esperadas_codigos=("codigoestacion", _unir_codigos),
        )
    )

    columnas_geo = ["codigoestacion", "codigo_municipio_canonico"]
    aportes = diario.merge(
        estaciones[columnas_geo],
        on="codigoestacion",
        how="inner",
        validate="many_to_one",
    ).rename(columns={"codigo_municipio_canonico": "codigo_municipio"})
    resumen_aportes = _resumir_aportes_estacion(aportes)

    fechas = pd.DataFrame({"fecha": pd.date_range(inicio, fin, freq="D")})
    base_municipios = municipios[
        [
            "codigo_departamento",
            "codigo_municipio",
            "Nombre Departamento",
            "Nombre Municipio",
        ]
    ].rename(
        columns={
            "Nombre Departamento": "departamento",
            "Nombre Municipio": "municipio",
        }
    )
    resultado = base_municipios.merge(fechas, how="cross")
    resultado = resultado.merge(
        red_estatica,
        on="codigo_municipio",
        how="left",
        validate="many_to_one",
    )
    resultado = resultado.merge(
        esperadas,
        on=["codigo_municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )
    resultado = resultado.merge(
        resumen_aportes,
        on=["codigo_municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )

    columnas_conteo = [
        "estaciones_canonicas_total",
        "estaciones_esperadas",
        "estaciones_con_fila",
        "estaciones_con_dato",
        "aportes_estacion_requieren_revision",
    ]
    for columna in columnas_conteo:
        resultado[columna] = resultado[columna].fillna(0).astype(int)
    resultado["codigo_municipio"] = (
        resultado["codigo_municipio"].astype("string").str.zfill(5)
    )

    resultado["cobertura_filas_pct"] = (
        100 * resultado["estaciones_con_fila"] / resultado["estaciones_esperadas"]
    ).where(resultado["estaciones_esperadas"].gt(0))
    resultado["cobertura_estaciones_pct"] = (
        100 * resultado["estaciones_con_dato"] / resultado["estaciones_esperadas"]
    ).where(resultado["estaciones_esperadas"].gt(0))
    resultado["rango_estaciones_mm"] = (
        resultado["precipitacion_max_estaciones_mm"]
        - resultado["precipitacion_min_estaciones_mm"]
    )
    resultado["iqr_estaciones_mm"] = (
        resultado["precipitacion_q75_estaciones_mm"]
        - resultado["precipitacion_q25_estaciones_mm"]
    )

    calidad = pd.Series(
        "SIN_ESTACIONES_CANONICAS",
        index=resultado.index,
        dtype="string",
    )
    tiene_red = resultado["estaciones_canonicas_total"].gt(0)
    tiene_esperadas = resultado["estaciones_esperadas"].gt(0)
    tiene_dato = resultado["estaciones_con_dato"].gt(0)
    cobertura_suficiente = resultado["cobertura_estaciones_pct"].ge(
        cobertura_minima_pct
    )
    calidad.loc[tiene_red & ~tiene_esperadas] = "SIN_ESTACIONES_ESPERADAS_EN_FECHA"
    calidad.loc[tiene_esperadas & ~tiene_dato] = "SIN_DATOS_ACEPTADOS"
    calidad.loc[tiene_esperadas & tiene_dato & ~cobertura_suficiente] = (
        "COBERTURA_INSUFICIENTE"
    )
    calidad.loc[
        tiene_esperadas
        & tiene_dato
        & cobertura_suficiente
        & resultado["estaciones_con_dato"].eq(1)
    ] = "VALIDO_UNA_ESTACION"
    calidad.loc[
        tiene_esperadas
        & cobertura_suficiente
        & resultado["estaciones_con_dato"].gt(1)
    ] = "VALIDO_MULTIESTACION"
    resultado["calidad_municipio_dia"] = calidad
    resultado["es_valido_municipio_dia"] = calidad.str.startswith("VALIDO_")
    resultado["requiere_revision_cobertura"] = calidad.eq(
        "COBERTURA_INSUFICIENTE"
    )
    resultado["precipitacion_municipal_mm"] = resultado[
        "precipitacion_mediana_estaciones_mm"
    ].where(resultado["es_valido_municipio_dia"]).astype("Float64")
    resultado["cobertura_minima_regla_pct"] = float(cobertura_minima_pct)
    resultado["regla_agregacion"] = AGGREGATION_VERSION

    if resultado.duplicated(list(CLAVE_MUNICIPIO_DIA)).any():
        raise RuntimeError("La agregacion produjo llaves municipio-dia repetidas.")
    if (
        resultado.loc[
            ~resultado["es_valido_municipio_dia"],
            "precipitacion_municipal_mm",
        ]
        .notna()
        .any()
    ):
        raise RuntimeError("Una fila municipal no valida recibio precipitacion.")
    filas_incompletas = (
        resultado["estaciones_con_fila"].gt(resultado["estaciones_esperadas"])
        | resultado["estaciones_con_dato"].gt(resultado["estaciones_con_fila"])
    )
    if filas_incompletas.any():
        raise RuntimeError("Los conteos de cobertura municipal son incoherentes.")

    resumen = (
        resultado.groupby(
            ["codigo_departamento", "departamento", "codigo_municipio", "municipio"],
            as_index=False,
        )
        .agg(
            estaciones_canonicas_total=("estaciones_canonicas_total", "max"),
            dias_calendario=("fecha", "size"),
            dias_con_estacion_esperada=(
                "estaciones_esperadas",
                lambda serie: int(serie.gt(0).sum()),
            ),
            dias_validos=("es_valido_municipio_dia", "sum"),
            dias_sin_datos_aceptados=(
                "calidad_municipio_dia",
                lambda serie: int(serie.eq("SIN_DATOS_ACEPTADOS").sum()),
            ),
            dias_cobertura_insuficiente=(
                "requiere_revision_cobertura",
                "sum",
            ),
            cobertura_mediana_pct=("cobertura_estaciones_pct", "median"),
        )
    )

    estaciones_no_canonicas = estaciones_diario - estaciones_geo
    filas_no_canonicas = diario["codigoestacion"].astype(str).isin(
        estaciones_no_canonicas
    )
    metricas = {
        "aggregation_version": AGGREGATION_VERSION,
        "estado": "COMPLETA",
        "fecha_inicio": inicio.date().isoformat(),
        "fecha_fin": fin.date().isoformat(),
        "municipios_objetivo": len(municipios),
        "municipios_con_estacion_canonica": int(
            red_estatica["codigo_municipio"].nunique()
        ),
        "municipios_sin_estacion_canonica": int(
            len(municipios) - red_estatica["codigo_municipio"].nunique()
        ),
        "estaciones_canonicas": len(estaciones),
        "estaciones_no_canonicas_excluidas": len(estaciones_no_canonicas),
        "filas_estacion_dia_entrada": len(diario),
        "filas_estacion_dia_canonicas": len(aportes),
        "filas_estacion_dia_excluidas": int(filas_no_canonicas.sum()),
        "valores_aceptados_estacion_excluidos": int(
            diario.loc[filas_no_canonicas, "precipitacion_diaria_mm"].notna().sum()
        ),
        "filas_municipio_dia": len(resultado),
        "filas_municipio_dia_validas": int(
            resultado["es_valido_municipio_dia"].sum()
        ),
        "filas_cobertura_insuficiente": int(
            resultado["requiere_revision_cobertura"].sum()
        ),
        "filas_sin_datos_aceptados": int(
            resultado["calidad_municipio_dia"].eq("SIN_DATOS_ACEPTADOS").sum()
        ),
        "cobertura_minima_pct": float(cobertura_minima_pct),
        "estadistica_principal": "MEDIANA_NO_PONDERADA",
    }
    return MunicipalAggregationResult(
        diario_municipal=resultado.sort_values(
            ["codigo_municipio", "fecha"]
        ).reset_index(drop=True),
        resumen_municipio=resumen.sort_values("codigo_municipio").reset_index(
            drop=True
        ),
        metricas=metricas,
    )
