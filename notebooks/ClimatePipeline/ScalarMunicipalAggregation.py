"""Agregación municipio-día para variables meteorológicas escalares."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from PrecipitationMunicipalAggregation import (
    _expandir_estaciones_esperadas,
    _unir_codigos,
    validar_divipola_objetivo,
    validar_estaciones_canonicas,
)


AGGREGATION_VERSION = "variable_escalar_municipio_dia_v1"
CLAVE_MUNICIPIO_DIA = ("codigo_municipio", "fecha")


@dataclass(slots=True)
class ScalarMunicipalAggregationResult:
    diario_municipal: pd.DataFrame
    resumen_municipio: pd.DataFrame
    metricas: dict[str, Any]


def agregar_escalar_municipal(
    diario_estacion: pd.DataFrame,
    estaciones_canonicas: pd.DataFrame,
    divipola: pd.DataFrame,
    fecha_inicio: str | pd.Timestamp,
    fecha_fin: str | pd.Timestamp,
    cobertura_minima_pct: float = 50.0,
) -> ScalarMunicipalAggregationResult:
    requeridas = {
        "variable",
        "dataset_id",
        "departamento",
        "codigoestacion",
        "fecha",
        "valor_diario",
        "unidad_valor",
        "calidad_dia",
        "requiere_revision",
    }
    faltantes = sorted(requeridas - set(diario_estacion.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del escalar estación-día: {faltantes}.")
    if not 0 < cobertura_minima_pct <= 100:
        raise ValueError("La cobertura mínima debe estar entre 0 y 100.")
    inicio, fin = pd.Timestamp(fecha_inicio), pd.Timestamp(fecha_fin)
    if pd.isna(inicio) or pd.isna(fin) or inicio > fin:
        raise ValueError("El intervalo temporal es inválido.")

    diario = diario_estacion.copy()
    diario["fecha"] = pd.to_datetime(diario["fecha"], errors="coerce")
    diario["valor_diario"] = pd.to_numeric(
        diario["valor_diario"], errors="coerce"
    ).astype("Float64")
    if diario["fecha"].isna().any():
        raise ValueError("El clima estación-día contiene fechas inválidas.")
    if diario.duplicated(["departamento", "codigoestacion", "fecha"]).any():
        raise ValueError("El clima contiene llaves estación-día repetidas.")
    variables = set(diario["variable"].dropna().astype(str))
    unidades = set(diario["unidad_valor"].dropna().astype(str))
    if len(variables) != 1 or len(unidades) != 1:
        raise ValueError("La entrada debe contener una sola variable y unidad.")
    variable, unidad = variables.pop(), unidades.pop()
    diario = diario.loc[diario["fecha"].between(inicio, fin)].copy()
    estaciones = validar_estaciones_canonicas(estaciones_canonicas)
    municipios = validar_divipola_objetivo(divipola)

    estaciones_diario = set(diario["codigoestacion"].astype(str))
    relevantes = set(
        estaciones.loc[
            estaciones["fecha_inicio_clima"].le(fin)
            & estaciones["fecha_fin_clima"].ge(inicio),
            "codigoestacion",
        ].astype(str)
    )
    faltantes_historia = sorted(relevantes - estaciones_diario)
    if faltantes_historia:
        raise ValueError(
            "Hay estaciones canónicas sin historia diaria: "
            f"{faltantes_historia[:10]}."
        )

    red = (
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
    aportes = diario.merge(
        estaciones[["codigoestacion", "codigo_municipio_canonico"]],
        on="codigoestacion",
        how="inner",
        validate="many_to_one",
    ).rename(columns={"codigo_municipio_canonico": "codigo_municipio"})
    grupos = aportes.groupby(["codigo_municipio", "fecha"], as_index=False)
    conteos = grupos.agg(
        estaciones_con_fila=("codigoestacion", "nunique"),
        estaciones_con_dato=("valor_diario", "count"),
        aportes_requieren_revision=("requiere_revision", "sum"),
    )
    aceptados = aportes.loc[aportes["valor_diario"].notna()]
    estadisticas = (
        aceptados.groupby(["codigo_municipio", "fecha"], as_index=False)
        .agg(
            estaciones_con_dato_codigos=("codigoestacion", _unir_codigos),
            valor_media_estaciones=("valor_diario", "mean"),
            valor_mediana_estaciones=("valor_diario", "median"),
            valor_min_estaciones=("valor_diario", "min"),
            valor_max_estaciones=("valor_diario", "max"),
            valor_std_estaciones=("valor_diario", "std"),
        )
    )
    aportes_resumen = conteos.merge(
        estadisticas,
        on=["codigo_municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )

    base = municipios[
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
    resultado = base.merge(
        pd.DataFrame({"fecha": pd.date_range(inicio, fin, freq="D")}),
        how="cross",
    )
    for tabla in (red, esperadas, aportes_resumen):
        claves = (
            ["codigo_municipio"]
            if "fecha" not in tabla.columns
            else ["codigo_municipio", "fecha"]
        )
        resultado = resultado.merge(tabla, on=claves, how="left")
    for columna in (
        "estaciones_canonicas_total",
        "estaciones_esperadas",
        "estaciones_con_fila",
        "estaciones_con_dato",
        "aportes_requieren_revision",
    ):
        resultado[columna] = resultado[columna].fillna(0).astype(int)
    resultado["cobertura_estaciones_pct"] = (
        100 * resultado["estaciones_con_dato"] / resultado["estaciones_esperadas"]
    ).where(resultado["estaciones_esperadas"].gt(0))
    calidad = pd.Series("SIN_ESTACIONES_CANONICAS", index=resultado.index)
    esperada = resultado["estaciones_esperadas"].gt(0)
    con_dato = resultado["estaciones_con_dato"].gt(0)
    suficiente = resultado["cobertura_estaciones_pct"].ge(cobertura_minima_pct)
    calidad.loc[esperada & ~con_dato] = "SIN_DATOS_ACEPTADOS"
    calidad.loc[esperada & con_dato & ~suficiente] = "COBERTURA_INSUFICIENTE"
    calidad.loc[esperada & suficiente & resultado["estaciones_con_dato"].eq(1)] = (
        "VALIDO_UNA_ESTACION"
    )
    calidad.loc[esperada & suficiente & resultado["estaciones_con_dato"].gt(1)] = (
        "VALIDO_MULTIESTACION"
    )
    resultado["variable"] = variable
    resultado["unidad_valor"] = unidad
    resultado["calidad_municipio_dia"] = calidad.astype("string")
    resultado["es_valido_municipio_dia"] = calidad.str.startswith("VALIDO_")
    resultado["valor_municipal"] = resultado["valor_mediana_estaciones"].where(
        resultado["es_valido_municipio_dia"]
    ).astype("Float64")
    resultado["cobertura_minima_regla_pct"] = float(cobertura_minima_pct)
    resultado["regla_agregacion"] = AGGREGATION_VERSION
    if resultado.duplicated(list(CLAVE_MUNICIPIO_DIA)).any():
        raise RuntimeError("La agregación produjo llaves municipio-día repetidas.")

    resumen = (
        resultado.groupby(
            ["codigo_departamento", "departamento", "codigo_municipio", "municipio"],
            as_index=False,
        )
        .agg(
            estaciones_canonicas_total=("estaciones_canonicas_total", "max"),
            dias_calendario=("fecha", "size"),
            dias_validos=("es_valido_municipio_dia", "sum"),
            cobertura_mediana_pct=("cobertura_estaciones_pct", "median"),
        )
    )
    metricas = {
        "aggregation_version": AGGREGATION_VERSION,
        "variable": variable,
        "unidad": unidad,
        "fecha_inicio": inicio.date().isoformat(),
        "fecha_fin": fin.date().isoformat(),
        "municipios_objetivo": len(municipios),
        "estaciones_canonicas": len(estaciones),
        "filas_estacion_dia_entrada": len(diario),
        "filas_municipio_dia": len(resultado),
        "filas_municipio_dia_validas": int(
            resultado["es_valido_municipio_dia"].sum()
        ),
        "cobertura_minima_pct": float(cobertura_minima_pct),
        "estadistica_principal": "MEDIANA_NO_PONDERADA",
    }
    return ScalarMunicipalAggregationResult(
        resultado.sort_values(["codigo_municipio", "fecha"]).reset_index(drop=True),
        resumen.sort_values("codigo_municipio").reset_index(drop=True),
        metricas,
    )
