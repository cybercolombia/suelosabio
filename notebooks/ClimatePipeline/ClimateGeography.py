"""Auditoria trazable de estaciones climaticas y catalogos geograficos."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


GEOGRAPHY_VERSION = "climate_station_geography_v3"
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
COLUMNAS_DIARIAS_BASE_REQUERIDAS = (
    "variable",
    "dataset_id",
    "departamento",
    "codigoestacion",
    "fecha",
    "municipios_observados",
    "nombres_estacion_observados",
    "latitud_mediana",
    "longitud_mediana",
)
COLUMNAS_VALOR_DIARIO = ("precipitacion_diaria_mm", "valor_diario")
COLUMNAS_POLIGONOS_REQUERIDAS = (
    "DPTO_CCDGO",
    "MPIO_CCDGO",
    "MPIO_CNMBR",
    "DEPTO",
)


@dataclass(slots=True)
class GeographyAuditResult:
    catalogo_climatico: pd.DataFrame
    estaciones_candidatas: pd.DataFrame
    estaciones_revision: pd.DataFrame
    estaciones_excluidas: pd.DataFrame
    divipola_objetivo: pd.DataFrame
    resumen: pd.DataFrame
    metricas: dict[str, Any]
    municipios_geograficos: Any | None = None


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


def _motivo_exclusion_alcance(departamento_normalizado: str) -> str:
    if departamento_normalizado == "BOGOTA D C":
        return "BOGOTA_D_C_EXCLUIDA_DEL_ALCANCE"
    if departamento_normalizado not in DEPARTAMENTOS_OBJETIVO:
        return "DEPARTAMENTO_FUERA_DEL_ALCANCE"
    return ""


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


def cargar_poligonos_municipales(
    ruta: str | Path,
    capa: str,
) -> Any:
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise ImportError(
            "Se necesita geopandas para leer y validar los poligonos municipales."
        ) from exc

    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el GeoPackage municipal: {ruta}")
    capas = gpd.list_layers(ruta)
    if capa not in set(capas["name"]):
        disponibles = ", ".join(capas["name"].astype(str))
        raise ValueError(
            f"No existe la capa {capa!r} en {ruta}. Disponibles: {disponibles}."
        )
    return gpd.read_file(ruta, layer=capa)


def validar_poligonos_municipales(
    poligonos: Any,
    divipola: pd.DataFrame,
) -> Any:
    faltantes = sorted(
        set(COLUMNAS_POLIGONOS_REQUERIDAS) - set(poligonos.columns)
    )
    if faltantes:
        raise ValueError(f"Faltan columnas de poligonos municipales: {faltantes}.")
    if not hasattr(poligonos, "geometry"):
        raise TypeError("La capa municipal no es un GeoDataFrame.")
    if poligonos.crs is None:
        raise ValueError("La capa municipal no declara un sistema de coordenadas.")

    tabla = poligonos.to_crs("EPSG:4326").copy()
    tabla["codigo_departamento_poligono"] = (
        tabla["DPTO_CCDGO"].astype("string").str.strip().str.zfill(2)
    )
    tabla["codigo_municipio_poligono"] = (
        tabla["codigo_departamento_poligono"]
        + tabla["MPIO_CCDGO"].astype("string").str.strip().str.zfill(3)
    )
    tabla["departamento_poligono"] = tabla["DEPTO"].astype("string").str.strip()
    tabla["municipio_poligono"] = tabla["MPIO_CNMBR"].astype("string").str.strip()

    codigos_objetivo = set(DEPARTAMENTOS_OBJETIVO.values())
    tabla = tabla.loc[
        tabla["codigo_departamento_poligono"].isin(codigos_objetivo)
    ].copy()
    if tabla["codigo_municipio_poligono"].duplicated().any():
        raise ValueError("La capa municipal contiene codigos DIVIPOLA repetidos.")
    if tabla.geometry.isna().any() or tabla.geometry.is_empty.any():
        raise ValueError("La capa municipal contiene geometrías nulas o vacias.")
    if not tabla.geometry.is_valid.all():
        invalidas = int((~tabla.geometry.is_valid).sum())
        raise ValueError(
            f"La capa municipal contiene {invalidas} geometrías invalidas."
        )

    div = (
        divipola
        if "codigo_municipio" in divipola.columns
        else validar_divipola(divipola)
    )
    codigos_divipola = set(
        div.loc[
            div["codigo_departamento"].isin(codigos_objetivo),
            "codigo_municipio",
        ]
    )
    codigos_poligono = set(tabla["codigo_municipio_poligono"])
    if codigos_poligono != codigos_divipola:
        faltan = sorted(codigos_divipola - codigos_poligono)
        sobran = sorted(codigos_poligono - codigos_divipola)
        raise ValueError(
            "Los poligonos no concuerdan con DIVIPOLA. "
            f"Faltan: {faltan[:10]}; sobran: {sobran[:10]}."
        )
    return tabla[
        [
            "codigo_departamento_poligono",
            "codigo_municipio_poligono",
            "departamento_poligono",
            "municipio_poligono",
            "geometry",
        ]
    ].sort_values("codigo_municipio_poligono").reset_index(drop=True)


def incorporar_asignaciones_espaciales(
    candidatos: pd.DataFrame,
    coincidencias: pd.DataFrame,
) -> pd.DataFrame:
    """Clasifica coincidencias punto-poligono sin ocultar conflictos de catalogo."""
    requeridas = {
        "codigoestacion",
        "codigo_municipio",
        "departamento_ideam_norm",
        "departamento_ideam_en_alcance",
        "motivos_revision_geografica",
    }
    faltantes = sorted(requeridas - set(candidatos.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas de candidatos geograficos: {faltantes}.")
    columnas_coincidencia = {
        "codigoestacion",
        "codigo_departamento_poligono",
        "codigo_municipio_poligono",
        "departamento_poligono",
        "municipio_poligono",
    }
    faltantes = sorted(columnas_coincidencia - set(coincidencias.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas del cruce espacial: {faltantes}.")

    def unir(serie: pd.Series) -> str:
        return " | ".join(sorted(set(serie.dropna().astype(str))))

    if coincidencias.empty:
        resumen_espacial = pd.DataFrame(
            columns=[
                "codigoestacion",
                "coincidencias_poligono",
                "codigo_departamento_poligono",
                "codigo_municipio_espacial",
                "departamento_espacial",
                "municipio_espacial",
            ]
        )
    else:
        resumen_espacial = (
            coincidencias.groupby("codigoestacion", as_index=False)
            .agg(
                coincidencias_poligono=(
                    "codigo_municipio_poligono",
                    "nunique",
                ),
                codigo_departamento_poligono=(
                    "codigo_departamento_poligono",
                    unir,
                ),
                codigo_municipio_espacial=(
                    "codigo_municipio_poligono",
                    unir,
                ),
                departamento_espacial=("departamento_poligono", unir),
                municipio_espacial=("municipio_poligono", unir),
            )
        )

    resultado = candidatos.copy()
    resultado["alertas_catalogo_previas"] = resultado[
        "motivos_revision_geografica"
    ]
    resultado = resultado.drop(
        columns=[
            "asignacion_metodo",
            "asignacion_canonica",
            "estado_asignacion",
            "requiere_revision_geografica",
        ],
        errors="ignore",
    )
    resultado = resultado.merge(
        resumen_espacial,
        on="codigoestacion",
        how="left",
        validate="one_to_one",
    )
    resultado["coincidencias_poligono"] = (
        resultado["coincidencias_poligono"].fillna(0).astype(int)
    )
    resultado["codigo_municipio_cercano"] = pd.Series(
        pd.NA,
        index=resultado.index,
        dtype="string",
    )
    resultado["municipio_cercano"] = pd.Series(
        pd.NA,
        index=resultado.index,
        dtype="string",
    )
    resultado["distancia_poligono_m"] = pd.Series(
        float("nan"),
        index=resultado.index,
        dtype="float64",
    )

    una = resultado["coincidencias_poligono"].eq(1)
    catalogo_conocido = resultado["codigo_municipio"].notna()
    codigo_coincide = resultado["codigo_municipio"].astype("string").eq(
        resultado["codigo_municipio_espacial"].astype("string")
    ).fillna(False)
    codigo_departamento_esperado = resultado["departamento_ideam_norm"].map(
        DEPARTAMENTOS_OBJETIVO
    )
    departamento_coincide = codigo_departamento_esperado.eq(
        resultado["codigo_departamento_poligono"]
    ).fillna(False)
    en_alcance = resultado["departamento_ideam_en_alcance"].fillna(False)
    resultado["motivo_exclusion_alcance"] = resultado[
        "departamento_ideam_norm"
    ].map(_motivo_exclusion_alcance)
    resultado["excluida_alcance"] = resultado[
        "motivo_exclusion_alcance"
    ].ne("")
    resultado["poligono_coincide_catalogo"] = (
        una & catalogo_conocido & codigo_coincide
    )
    resultado["poligono_resuelve_catalogo"] = una & ~catalogo_conocido
    resultado["asignacion_canonica"] = (
        una
        & en_alcance
        & departamento_coincide
        & (~catalogo_conocido | codigo_coincide)
    )
    resultado["codigo_municipio_canonico"] = resultado[
        "codigo_municipio_espacial"
    ].where(resultado["asignacion_canonica"])
    resultado["municipio_canonico"] = resultado["municipio_espacial"].where(
        resultado["asignacion_canonica"]
    )

    metodos = pd.Series(
        "SIN_ASIGNACION_ESPACIAL",
        index=resultado.index,
        dtype="string",
    )
    metodos.loc[resultado["poligono_coincide_catalogo"]] = (
        "PUNTO_EN_POLIGONO_CONFIRMA_CATALOGO"
    )
    metodos.loc[
        resultado["poligono_resuelve_catalogo"]
        & resultado["asignacion_canonica"]
    ] = "PUNTO_EN_POLIGONO_RESUELVE_CATALOGO"
    metodos.loc[
        una & catalogo_conocido & ~codigo_coincide
    ] = "CONFLICTO_CATALOGO_POLIGONO"
    metodos.loc[resultado["coincidencias_poligono"].gt(1)] = (
        "PUNTO_INTERSECTA_MULTIPLES_POLIGONOS"
    )
    resultado["asignacion_metodo"] = metodos

    def motivos(fila: pd.Series) -> str:
        alertas = []
        if not bool(fila["departamento_ideam_en_alcance"]):
            alertas.append("FUERA_ALCANCE_GEOGRAFICO")
        if fila["coincidencias_poligono"] == 0:
            alertas.append("SIN_POLIGONO_CONTENEDOR")
        elif fila["coincidencias_poligono"] > 1:
            alertas.append("MULTIPLES_POLIGONOS_INTERSECTADOS")
        else:
            if not departamento_coincide.loc[fila.name]:
                alertas.append("DEPARTAMENTO_POLIGONO_DISCREPA_IDEAM")
            if pd.notna(fila["codigo_municipio"]) and not codigo_coincide.loc[
                fila.name
            ]:
                alertas.append("CATALOGO_POLIGONO_DISCREPAN")
        return "|".join(alertas)

    resultado["motivos_revision_geografica"] = resultado.apply(motivos, axis=1)
    resultado["requiere_revision_geografica"] = (
        ~resultado["asignacion_canonica"]
        & ~resultado["excluida_alcance"]
    )
    resultado["estado_asignacion"] = "REQUIERE_REVISION_ESPACIAL"
    resultado.loc[
        resultado["asignacion_canonica"],
        "estado_asignacion",
    ] = "ASIGNACION_CANONICA"
    resultado.loc[
        resultado["excluida_alcance"],
        "estado_asignacion",
    ] = "EXCLUIDA_FUERA_ALCANCE"
    return resultado


def cruzar_estaciones_poligonos(
    candidatos: pd.DataFrame,
    poligonos: Any,
) -> pd.DataFrame:
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise ImportError(
            "Se necesita geopandas para ejecutar el cruce punto-en-poligono."
        ) from exc

    if candidatos[["LONGITUD", "LATITUD"]].isna().any().any():
        raise ValueError("Hay estaciones IDEAM sin coordenadas para el cruce espacial.")
    puntos = gpd.GeoDataFrame(
        candidatos[["codigoestacion"]].copy(),
        geometry=gpd.points_from_xy(
            candidatos["LONGITUD"],
            candidatos["LATITUD"],
        ),
        crs="EPSG:4326",
    )
    coincidencias = gpd.sjoin(
        puntos,
        poligonos,
        how="inner",
        predicate="intersects",
    )
    columnas = [
        "codigoestacion",
        "codigo_departamento_poligono",
        "codigo_municipio_poligono",
        "departamento_poligono",
        "municipio_poligono",
    ]
    resultado = incorporar_asignaciones_espaciales(
        candidatos,
        pd.DataFrame(coincidencias[columnas]),
    )
    estaciones_con_poligono = set(coincidencias["codigoestacion"])
    puntos_sin_poligono = puntos.loc[
        ~puntos["codigoestacion"].isin(estaciones_con_poligono)
    ]
    if puntos_sin_poligono.empty:
        return resultado

    proyeccion_metrica = "EPSG:9377"
    cercanos = gpd.sjoin_nearest(
        puntos_sin_poligono.to_crs(proyeccion_metrica),
        poligonos.to_crs(proyeccion_metrica),
        how="left",
        distance_col="distancia_poligono_m",
    )
    cercanos = cercanos[
        [
            "codigoestacion",
            "codigo_municipio_poligono",
            "municipio_poligono",
            "distancia_poligono_m",
        ]
    ].rename(
        columns={
            "codigo_municipio_poligono": "codigo_municipio_cercano_nuevo",
            "municipio_poligono": "municipio_cercano_nuevo",
            "distancia_poligono_m": "distancia_poligono_m_nueva",
        }
    )
    cercanos = cercanos.sort_values(
        ["codigoestacion", "distancia_poligono_m_nueva"]
    ).drop_duplicates("codigoestacion")
    resultado = resultado.merge(
        pd.DataFrame(cercanos),
        on="codigoestacion",
        how="left",
        validate="one_to_one",
    )
    resultado["codigo_municipio_cercano"] = resultado[
        "codigo_municipio_cercano_nuevo"
    ].combine_first(resultado["codigo_municipio_cercano"])
    resultado["municipio_cercano"] = resultado[
        "municipio_cercano_nuevo"
    ].combine_first(resultado["municipio_cercano"])
    resultado["distancia_poligono_m"] = resultado[
        "distancia_poligono_m_nueva"
    ].combine_first(resultado["distancia_poligono_m"])
    return resultado.drop(
        columns=[
            "codigo_municipio_cercano_nuevo",
            "municipio_cercano_nuevo",
            "distancia_poligono_m_nueva",
        ]
    )


def construir_catalogo_climatico(diario: pd.DataFrame) -> pd.DataFrame:
    faltantes = sorted(
        set(COLUMNAS_DIARIAS_BASE_REQUERIDAS) - set(diario.columns)
    )
    if faltantes:
        raise ValueError(f"Faltan columnas del clima diario curado: {faltantes}.")
    columnas_valor = [
        columna for columna in COLUMNAS_VALOR_DIARIO if columna in diario.columns
    ]
    if len(columnas_valor) != 1:
        raise ValueError(
            "El clima diario debe contener exactamente una columna de valor: "
            f"{COLUMNAS_VALOR_DIARIO}."
        )
    columna_valor = columnas_valor[0]

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
            dias_clima_aceptado=(columna_valor, "count"),
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


def construir_catalogo_ideam_de_referencia(
    diario: pd.DataFrame,
    estaciones_referencia: pd.DataFrame,
) -> pd.DataFrame:
    """Completa el catálogo IDEAM desde una auditoría previa y el clima.

    Esta ruta de contingencia permite reutilizar las columnas IDEAM conservadas
    por una geografía canónica previa cuando el CSV fuente no está montado. Las
    estaciones nuevas conservan explícitamente ``Estado=DESCONOCIDO`` y usan
    sus metadatos climáticos; no se inventan altitud ni fechas administrativas.
    """
    catalogo = construir_catalogo_climatico(diario)
    codigos = set(catalogo["codigoestacion"].astype(str))
    columnas = list(COLUMNAS_ESTACIONES_REQUERIDAS) + [
        "Categoria",
        "Tecnologia",
        "Entidad",
    ]
    referencia = estaciones_referencia.copy()
    if "Altitud" not in referencia and "altitud_ideam_m" in referencia:
        referencia["Altitud"] = referencia["altitud_ideam_m"]
    faltantes_referencia = sorted(set(columnas) - set(referencia.columns))
    if faltantes_referencia:
        raise ValueError(
            "La geografía de referencia no conserva el catálogo IDEAM: "
            f"{faltantes_referencia}."
        )
    referencia = referencia.loc[
        referencia["Codigo"].astype("string").isin(codigos),
        columnas,
    ].drop_duplicates("Codigo")
    conocidos = set(referencia["Codigo"].dropna().astype(str))
    nuevos = catalogo.loc[
        ~catalogo["codigoestacion"].astype(str).isin(conocidos)
    ].copy()
    if not nuevos.empty:
        nuevos_ideam = pd.DataFrame(
            {
                "Codigo": nuevos["codigoestacion"],
                "Nombre": nuevos["nombres_estacion_reportados"],
                "Estado": "DESCONOCIDO",
                "Departamento": nuevos["departamento"],
                "Municipio": nuevos["municipios_reportados"].map(
                    lambda value: str(value).split(" | ")[0]
                ),
                "Altitud": pd.NA,
                "LONGITUD": nuevos["longitud_clima"],
                "LATITUD": nuevos["latitud_clima"],
                "Fecha_instalacion": pd.NA,
                "Fecha_suspension": pd.NA,
                "Categoria": pd.NA,
                "Tecnologia": pd.NA,
                "Entidad": pd.NA,
            }
        )
        referencia = pd.concat(
            [referencia, nuevos_ideam[columnas]],
            ignore_index=True,
        )
    if set(referencia["Codigo"].dropna().astype(str)) != codigos:
        raise RuntimeError(
            "No fue posible reconstruir el catálogo de todas las estaciones."
        )
    return referencia.sort_values("Codigo").reset_index(drop=True)


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
    cruce["motivo_exclusion_alcance"] = cruce[
        "departamento_ideam_norm"
    ].map(_motivo_exclusion_alcance)
    cruce["excluida_alcance"] = cruce["motivo_exclusion_alcance"].ne("")

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
    cruce["requiere_revision_geografica"] = (
        cruce["motivos_revision_geografica"].ne("")
        & ~cruce["excluida_alcance"]
    )
    cruce["estado_asignacion"] = "CANDIDATO_CATALOGO_OK"
    cruce.loc[
        cruce["requiere_revision_geografica"],
        "estado_asignacion",
    ] = "CANDIDATO_REQUIERE_REVISION"
    cruce.loc[
        cruce["excluida_alcance"],
        "estado_asignacion",
    ] = "EXCLUIDA_FUERA_ALCANCE"
    return cruce.drop(columns=["cruce_ideam"]), div


def auditar_geografia(
    diario: pd.DataFrame,
    estaciones_ideam: pd.DataFrame,
    divipola: pd.DataFrame,
    umbral_coordenadas_grados: float = 0.001,
    poligonos_municipales: Any | None = None,
) -> GeographyAuditResult:
    catalogo = construir_catalogo_climatico(diario)
    candidatos, div_completa = cruzar_catalogos(
        catalogo,
        estaciones_ideam,
        divipola,
        umbral_coordenadas_grados=umbral_coordenadas_grados,
    )
    municipios_geograficos = None
    if poligonos_municipales is not None:
        municipios_geograficos = validar_poligonos_municipales(
            poligonos_municipales,
            div_completa,
        )
        candidatos = cruzar_estaciones_poligonos(
            candidatos,
            municipios_geograficos,
        )
    revisiones = candidatos.loc[
        candidatos["requiere_revision_geografica"]
    ].copy()
    excluidas = candidatos.loc[candidatos["excluida_alcance"]].copy()
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
            excluidas_alcance=("excluida_alcance", "sum"),
            varios_municipios=(
                "municipios_reportados_cantidad",
                lambda serie: int(serie.gt(1).sum()),
            ),
            coordenada_difiere=("coordenada_difiere_umbral", "sum"),
            asignaciones_canonicas=("asignacion_canonica", "sum"),
        )
    )
    con_poligonos = municipios_geograficos is not None
    metricas = {
        "geography_version": GEOGRAPHY_VERSION,
        "estado": (
            "COMPLETA_CON_REVISION_PENDIENTE"
            if con_poligonos and len(revisiones)
            else "COMPLETA"
            if con_poligonos
            else "COMPLETA_SIN_POLIGONOS"
        ),
        "estaciones_climaticas": len(catalogo),
        "estaciones_encontradas_ideam": int(
            candidatos["catalogo_ideam_encontrado"].sum()
        ),
        "estaciones_divipola_resuelta": int(
            candidatos["divipola_resuelta"].sum()
        ),
        "estaciones_revision": len(revisiones),
        "estaciones_excluidas_alcance": len(excluidas),
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
        "municipios_poligonos_objetivo": (
            len(municipios_geograficos) if con_poligonos else 0
        ),
        "umbral_coordenadas_grados": float(umbral_coordenadas_grados),
        "asignaciones_canonicas": int(
            candidatos["asignacion_canonica"].sum()
        ),
        "estaciones_sin_poligono_contenedor": int(
            candidatos.get(
                "coincidencias_poligono",
                pd.Series(0, index=candidatos.index),
            ).eq(0).sum()
        )
        if con_poligonos
        else 0,
        "estaciones_conflicto_catalogo_poligono": int(
            candidatos.get(
                "asignacion_metodo",
                pd.Series("", index=candidatos.index),
            ).eq("CONFLICTO_CATALOGO_POLIGONO").sum()
        )
        if con_poligonos
        else 0,
        "estaciones_resueltas_solo_poligono": int(
            candidatos.get(
                "asignacion_metodo",
                pd.Series("", index=candidatos.index),
            ).eq("PUNTO_EN_POLIGONO_RESUELVE_CATALOGO").sum()
        )
        if con_poligonos
        else 0,
    }
    return GeographyAuditResult(
        catalogo_climatico=catalogo,
        estaciones_candidatas=candidatos,
        estaciones_revision=revisiones,
        estaciones_excluidas=excluidas,
        divipola_objetivo=div_objetivo,
        resumen=resumen,
        metricas=metricas,
        municipios_geograficos=municipios_geograficos,
    )
