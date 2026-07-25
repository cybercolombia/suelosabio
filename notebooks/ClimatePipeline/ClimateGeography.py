"""Auditoria trazable de estaciones climaticas y catalogos geograficos."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

import pandas as pd


GEOGRAPHY_VERSION = "climate_station_geography_v1"
DEPARTAMENTOS_OBJETIVO = {
    "BOYACA": "15",
    "CUNDINAMARCA": "25",
}
COLUMNAS_ESTACIONES_REQUERIDAS = (
    "Codigo",
    "Nombre",
    "Estado",
    "Departamento",
    "Municipio",
    "Altitud",
    "LONGITUD",
    "LATITUD",
    "Fecha_instalacion",
    "Fecha_suspension",
)
COLUMNAS_DIVIPOLA_REQUERIDAS = (
    "Código Departamento",
    "Nombre Departamento",
    "Código Municipio",
    "Nombre Municipio",
    "longitud",
    "Latitud",
)
COLUMNAS_DIARIAS_REQUERIDAS = (
    "variable",
    "dataset_id",
    "departamento",
    "codigoestacion",
    "fecha",
    "precipitacion_diaria_mm",
    "municipios_observados",
    "nombres_estacion_observados",
    "latitud_mediana",
    "longitud_mediana",
)


@dataclass(slots=True)
class GeographyAuditResult:
    catalogo_climatico: pd.DataFrame
    estaciones_candidatas: pd.DataFrame
    estaciones_revision: pd.DataFrame
    divipola_objetivo: pd.DataFrame
    resumen: pd.DataFrame
    metricas: dict[str, Any]


def normalizar_nombre(valor: Any) -> str:
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ascii", errors="ignore").decode("ascii").upper()
    return re.sub(r"[^A-Z0-9]+", " ", texto).strip()


def preparar_tabla_serializable(tabla: pd.DataFrame) -> pd.DataFrame:
    """Reemplaza escalares nulos de pandas por valores serializables."""
    serializable = tabla.copy().astype(object)
    return serializable.where(pd.notna(serializable), None)


def _normalizar_departamento_catalogo(valor: Any) -> str:
    nombre = normalizar_nombre(valor)
    alias = {
        "BOGOTA": "BOGOTA D C",
        "BOGOTA DC": "BOGOTA D C",
    }
    return alias.get(nombre, nombre)


def _separar_etiquetas(serie: pd.Series) -> list[str]:
    return sorted(
        {
            etiqueta.strip()
            for valor in serie.dropna().astype(str)
            for etiqueta in valor.split(" | ")
            if etiqueta.strip()
        }
    )


def _unir_etiquetas(serie: pd.Series) -> str:
    return " | ".join(_separar_etiquetas(serie))


def _numero_colombiano(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(
        serie.astype("string").str.replace(",", ".", regex=False),
        errors="coerce",
    )


def validar_catalogo_ideam(estaciones: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_ESTACIONES_REQUERIDAS) - set(estaciones.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del catalogo IDEAM: {faltantes}.")

    tabla = estaciones.copy()
    tabla["Codigo"] = tabla["Codigo"].astype("string").str.strip()
    if tabla["Codigo"].isna().any() or tabla["Codigo"].eq("").any():
        raise ValueError("El catalogo IDEAM contiene codigos vacios.")
    if tabla["Codigo"].duplicated().any():
        raise ValueError("El catalogo IDEAM contiene codigos de estacion repetidos.")

    tabla["LONGITUD"] = pd.to_numeric(tabla["LONGITUD"], errors="coerce")
    tabla["LATITUD"] = pd.to_numeric(tabla["LATITUD"], errors="coerce")
    if tabla[["LONGITUD", "LATITUD"]].isna().any().any():
        raise ValueError("El catalogo IDEAM contiene coordenadas invalidas.")
    if not tabla["LONGITUD"].between(-180, 180).all():
        raise ValueError("El catalogo IDEAM contiene longitudes fuera de rango.")
    if not tabla["LATITUD"].between(-90, 90).all():
        raise ValueError("El catalogo IDEAM contiene latitudes fuera de rango.")

    tabla["altitud_ideam_m"] = pd.to_numeric(
        tabla["Altitud"].astype("string").str.replace(",", "", regex=False),
        errors="coerce",
    )
    tabla["departamento_ideam_norm"] = tabla["Departamento"].map(
        _normalizar_departamento_catalogo
    )
    tabla["municipio_ideam_norm"] = tabla["Municipio"].map(normalizar_nombre)
    return tabla


def validar_divipola(divipola: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_DIVIPOLA_REQUERIDAS) - set(divipola.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas DIVIPOLA: {faltantes}.")

    tabla = divipola.copy()
    tabla["codigo_departamento"] = (
        tabla["Código Departamento"].astype("string").str.strip().str.zfill(2)
    )
    tabla["codigo_municipio"] = (
        tabla["Código Municipio"].astype("string").str.strip().str.zfill(5)
    )
    if tabla["codigo_municipio"].duplicated().any():
        raise ValueError("DIVIPOLA contiene codigos municipales repetidos.")
    if not tabla["codigo_municipio"].str.fullmatch(r"\d{5}").all():
        raise ValueError("DIVIPOLA contiene codigos municipales invalidos.")

    tabla["departamento_divipola_norm"] = tabla["Nombre Departamento"].map(
        _normalizar_departamento_catalogo
    )
    tabla["municipio_divipola_norm"] = tabla["Nombre Municipio"].map(
        normalizar_nombre
    )
    tabla["longitud_referencia"] = _numero_colombiano(tabla["longitud"])
    tabla["latitud_referencia"] = _numero_colombiano(tabla["Latitud"])
    return tabla


def construir_catalogo_climatico(diario: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(set(COLUMNAS_DIARIAS_REQUERIDAS) - set(diario.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del clima diario curado: {faltantes}.")

    tabla = diario.copy()
    tabla["fecha"] = pd.to_datetime(tabla["fecha"], errors="coerce")
    tabla["latitud_mediana"] = pd.to_numeric(
        tabla["latitud_mediana"], errors="coerce"
    )
    tabla["longitud_mediana"] = pd.to_numeric(
        tabla["longitud_mediana"], errors="coerce"
    )
    if tabla["fecha"].isna().any():
        raise ValueError("El clima diario curado contiene fechas invalidas.")

    catalogo = (
        tabla.groupby(["departamento", "codigoestacion"], as_index=False)
        .agg(
            variables=("variable", _unir_etiquetas),
            fuentes=("dataset_id", _unir_etiquetas),
            fecha_inicio_clima=("fecha", "min"),
            fecha_fin_clima=("fecha", "max"),
            filas_estacion_dia=("fecha", "size"),
            dias_clima_aceptado=("precipitacion_diaria_mm", "count"),
            municipios_reportados=("municipios_observados", _unir_etiquetas),
            nombres_estacion_reportados=(
                "nombres_estacion_observados",
                _unir_etiquetas,
            ),
            latitud_clima=("latitud_mediana", "median"),
            longitud_clima=("longitud_mediana", "median"),
            latitud_clima_min=("latitud_mediana", "min"),
            latitud_clima_max=("latitud_mediana", "max"),
            longitud_clima_min=("longitud_mediana", "min"),
            longitud_clima_max=("longitud_mediana", "max"),
        )
    )
    catalogo["codigoestacion"] = (
        catalogo["codigoestacion"].astype("string").str.strip()
    )
    catalogo["departamento_fuente_norm"] = catalogo["departamento"].map(
        normalizar_nombre
    )
    catalogo["municipios_reportados_cantidad"] = catalogo[
        "municipios_reportados"
    ].map(lambda valor: len(valor.split(" | ")) if valor else 0)
    catalogo["desplazamiento_latitud"] = (
        catalogo["latitud_clima_max"] - catalogo["latitud_clima_min"]
    )
    catalogo["desplazamiento_longitud"] = (
        catalogo["longitud_clima_max"] - catalogo["longitud_clima_min"]
    )
    if catalogo["codigoestacion"].duplicated().any():
        raise RuntimeError("El catalogo climatico produjo estaciones repetidas.")
    return catalogo


def _municipio_catalogo_en_reportados(fila: pd.Series) -> bool:
    reportados = {
        normalizar_nombre(valor)
        for valor in str(fila["municipios_reportados"]).split(" | ")
        if valor
    }
    return fila["municipio_ideam_norm"] in reportados


def cruzar_catalogos(
    catalogo_climatico: pd.DataFrame,
    estaciones_ideam: pd.DataFrame,
    divipola: pd.DataFrame,
    umbral_coordenadas_grados: float = 0.001,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if umbral_coordenadas_grados < 0:
        raise ValueError("El umbral de coordenadas no puede ser negativo.")

    ideam = validar_catalogo_ideam(estaciones_ideam)
    div = validar_divipola(divipola)
    columnas_ideam = [
        "Codigo",
        "Nombre",
        "Categoria",
        "Tecnologia",
        "Estado",
        "Departamento",
        "Municipio",
        "altitud_ideam_m",
        "LONGITUD",
        "LATITUD",
        "Fecha_instalacion",
        "Fecha_suspension",
        "Entidad",
        "departamento_ideam_norm",
        "municipio_ideam_norm",
    ]
    cruce = catalogo_climatico.merge(
        ideam[columnas_ideam],
        left_on="codigoestacion",
        right_on="Codigo",
        how="left",
        validate="one_to_one",
        indicator="cruce_ideam",
    )
    cruce["catalogo_ideam_encontrado"] = cruce["cruce_ideam"].eq("both")
    cruce["departamento_fuente_coincide_ideam"] = (
        cruce["departamento_fuente_norm"]
        == cruce["departamento_ideam_norm"]
    )
    cruce["municipio_ideam_en_reportados"] = cruce.apply(
        _municipio_catalogo_en_reportados,
        axis=1,
    )
    cruce["diferencia_latitud_grados"] = (
        cruce["latitud_clima"] - cruce["LATITUD"]
    ).abs()
    cruce["diferencia_longitud_grados"] = (
        cruce["longitud_clima"] - cruce["LONGITUD"]
    ).abs()
    cruce["coordenada_difiere_umbral"] = (
        cruce["diferencia_latitud_grados"].gt(umbral_coordenadas_grados)
        | cruce["diferencia_longitud_grados"].gt(umbral_coordenadas_grados)
    ).fillna(True)
    cruce["departamento_ideam_en_alcance"] = cruce[
        "departamento_ideam_norm"
    ].isin(DEPARTAMENTOS_OBJETIVO)

    columnas_div = [
        "codigo_departamento",
        "codigo_municipio",
        "Nombre Departamento",
        "Nombre Municipio",
        "departamento_divipola_norm",
        "municipio_divipola_norm",
        "longitud_referencia",
        "latitud_referencia",
    ]
    cruce = cruce.merge(
        div[columnas_div],
        left_on=["departamento_ideam_norm", "municipio_ideam_norm"],
        right_on=["departamento_divipola_norm", "municipio_divipola_norm"],
        how="left",
        validate="many_to_one",
    )
    cruce["divipola_resuelta"] = cruce["codigo_municipio"].notna()
    cruce["asignacion_metodo"] = "CATALOGO_IDEAM_DIVIPOLA_SIN_POLIGONO"
    cruce["asignacion_canonica"] = False

    def motivos(fila: pd.Series) -> str:
        alertas = []
        if not fila["catalogo_ideam_encontrado"]:
            alertas.append("CATALOGO_IDEAM_NO_ENCONTRADO")
        if not fila["departamento_ideam_en_alcance"]:
            alertas.append("FUERA_ALCANCE_GEOGRAFICO")
        if not fila["departamento_fuente_coincide_ideam"]:
            alertas.append("DEPARTAMENTO_DISCREPANTE")
        if fila["municipios_reportados_cantidad"] > 1:
            alertas.append("MUNICIPIO_MULTIPLE")
        if not fila["municipio_ideam_en_reportados"]:
            alertas.append("MUNICIPIO_DISCREPANTE")
        if fila["coordenada_difiere_umbral"]:
            alertas.append("COORDENADA_DIFIERE")
        if not fila["divipola_resuelta"]:
            alertas.append("DIVIPOLA_NO_RESUELTA")
        return "|".join(alertas)

    cruce["motivos_revision_geografica"] = cruce.apply(motivos, axis=1)
    cruce["requiere_revision_geografica"] = cruce[
        "motivos_revision_geografica"
    ].ne("")
    cruce["estado_asignacion"] = cruce["requiere_revision_geografica"].map(
        {True: "CANDIDATO_REQUIERE_REVISION", False: "CANDIDATO_CATALOGO_OK"}
    )
    return cruce.drop(columns=["cruce_ideam"]), div


def auditar_geografia(
    diario: pd.DataFrame,
    estaciones_ideam: pd.DataFrame,
    divipola: pd.DataFrame,
    umbral_coordenadas_grados: float = 0.001,
) -> GeographyAuditResult:
    catalogo = construir_catalogo_climatico(diario)
    candidatos, div_completa = cruzar_catalogos(
        catalogo,
        estaciones_ideam,
        divipola,
        umbral_coordenadas_grados=umbral_coordenadas_grados,
    )
    revisiones = candidatos.loc[
        candidatos["requiere_revision_geografica"]
    ].copy()
    codigos_objetivo = set(DEPARTAMENTOS_OBJETIVO.values())
    div_objetivo = div_completa.loc[
        div_completa["codigo_departamento"].isin(codigos_objetivo)
    ].copy()

    resumen = (
        candidatos.groupby("departamento", as_index=False)
        .agg(
            estaciones=("codigoestacion", "nunique"),
            encontradas_ideam=("catalogo_ideam_encontrado", "sum"),
            divipola_resuelta=("divipola_resuelta", "sum"),
            requieren_revision=("requiere_revision_geografica", "sum"),
            varios_municipios=(
                "municipios_reportados_cantidad",
                lambda serie: int(serie.gt(1).sum()),
            ),
            coordenada_difiere=("coordenada_difiere_umbral", "sum"),
        )
    )
    metricas = {
        "geography_version": GEOGRAPHY_VERSION,
        "estado": "COMPLETA_SIN_POLIGONOS",
        "estaciones_climaticas": len(catalogo),
        "estaciones_encontradas_ideam": int(
            candidatos["catalogo_ideam_encontrado"].sum()
        ),
        "estaciones_divipola_resuelta": int(
            candidatos["divipola_resuelta"].sum()
        ),
        "estaciones_revision": len(revisiones),
        "estaciones_fuera_alcance": int(
            (~candidatos["departamento_ideam_en_alcance"]).sum()
        ),
        "estaciones_municipio_multiple": int(
            candidatos["municipios_reportados_cantidad"].gt(1).sum()
        ),
        "estaciones_coordenada_difiere": int(
            candidatos["coordenada_difiere_umbral"].sum()
        ),
        "municipios_divipola_objetivo": len(div_objetivo),
        "umbral_coordenadas_grados": float(umbral_coordenadas_grados),
        "asignaciones_canonicas": 0,
    }
    return GeographyAuditResult(
        catalogo_climatico=catalogo,
        estaciones_candidatas=candidatos,
        estaciones_revision=revisiones,
        divipola_objetivo=div_objetivo,
        resumen=resumen,
        metricas=metricas,
    )
