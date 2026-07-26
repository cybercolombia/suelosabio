"""Contratos v1 para transformar temperatura subdiaria a diaria por sensor."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any

import pandas as pd

from ClimateProcessingUtils import PartitionSpec


RULE_VERSION = "temperatura_diaria_v2"
CADENCIAS_OBSERVADAS_SEGUNDOS = (60, 120, 600, 3600)
RANGO_OPERATIVO_C = (-30.0, 60.0)
COLUMNAS_REQUERIDAS = (
    "codigoestacion",
    "codigosensor",
    "dataset_id",
    "departamento",
    "descripcionsensor",
    "fechaobservacion",
    "latitud",
    "longitud",
    "municipio",
    "nombreestacion",
    "unidadmedida",
    "valorobservado",
    "zonahidrografica",
)
CLAVE_OBSERVACION = ("codigoestacion", "codigosensor", "fechaobservacion")


CONTRATOS_TEMPERATURA = {
    "temperatura_ambiente": {
        "dataset_id": "sbwg-7ju4",
        "sensores": {"0068", "0071"},
        "descripcion": "AMBIENTE",
        "estadistico_principal": "MEDIA",
    },
    "temperatura_minima": {
        "dataset_id": "afdg-3zpb",
        "sensores": {"0070"},
        "descripcion": "MINIMA",
        "estadistico_principal": "MINIMO",
    },
    "temperatura_maxima": {
        "dataset_id": "ccvq-rp9s",
        "sensores": {"0069"},
        "descripcion": "MAXIMA",
        "estadistico_principal": "MAXIMO",
    },
}


@dataclass(slots=True)
class TemperatureProcessingResult:
    diario: pd.DataFrame
    cadencias: pd.DataFrame
    rechazados: pd.DataFrame
    conflictos: pd.DataFrame
    duplicados_eliminados: pd.DataFrame
    metricas: dict[str, Any]


def _normalizar_texto(valor: Any) -> Any:
    if pd.isna(valor):
        return pd.NA
    return unicodedata.normalize("NFC", str(valor).strip())


def _texto_sin_tildes(valor: Any) -> str:
    if pd.isna(valor):
        return ""
    texto = unicodedata.normalize("NFKD", str(valor))
    return texto.encode("ascii", errors="ignore").decode("ascii").upper()


def _agregar_motivo(motivos: pd.Series, mascara: pd.Series, motivo: str) -> None:
    mascara = mascara.fillna(False)
    motivos.loc[mascara & motivos.eq("")] = motivo
    motivos.loc[mascara & motivos.ne("") & ~motivos.str.contains(motivo, regex=False)] += (
        f"|{motivo}"
    )


def _validar_contrato(spec: PartitionSpec) -> dict[str, Any]:
    if spec.variable not in CONTRATOS_TEMPERATURA:
        raise ValueError(
            f"Variable de temperatura no soportada: {spec.variable}. "
            f"Use una de {sorted(CONTRATOS_TEMPERATURA)}."
        )
    contrato = CONTRATOS_TEMPERATURA[spec.variable]
    if spec.dataset_id != contrato["dataset_id"]:
        raise ValueError(
            f"{spec.variable} requiere la fuente {contrato['dataset_id']}; "
            f"se recibio {spec.dataset_id}."
        )
    return contrato


def _descripcion_corresponde(valor: Any, tipo: str) -> bool:
    texto = _texto_sin_tildes(valor)
    if "TEMPERATURA" not in texto or "AIRE" not in texto:
        return False
    if tipo == "MINIMA":
        return "MINIMA" in texto
    if tipo == "MAXIMA":
        return "MAXIMA" in texto
    return "MINIMA" not in texto and "MAXIMA" not in texto


def preparar_observaciones(
    crudo: pd.DataFrame,
    spec: PartitionSpec,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    contrato = _validar_contrato(spec)
    faltantes = sorted(set(COLUMNAS_REQUERIDAS) - set(crudo.columns))
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}.")

    tabla = crudo.loc[:, COLUMNAS_REQUERIDAS].copy()
    tabla["_orden_origen"] = range(len(tabla))
    for columna in (
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
        tabla[columna] = tabla[columna].map(_normalizar_texto).astype("string")

    tabla["departamento"] = tabla["departamento"].str.upper().str.replace(
        " ", "_", regex=False
    )
    tabla["unidadmedida"] = tabla["unidadmedida"].str.lower()
    tabla["fechaobservacion"] = pd.to_datetime(
        tabla["fechaobservacion"], errors="coerce"
    )
    for columna in ("valorobservado", "latitud", "longitud"):
        tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce")

    motivos = pd.Series("", index=tabla.index, dtype="string")
    _agregar_motivo(motivos, tabla["codigoestacion"].isna(), "estacion_nula")
    _agregar_motivo(motivos, tabla["codigosensor"].isna(), "sensor_nulo")
    _agregar_motivo(motivos, tabla["fechaobservacion"].isna(), "fecha_invalida")
    _agregar_motivo(motivos, tabla["valorobservado"].isna(), "valor_invalido")
    _agregar_motivo(
        motivos,
        tabla["valorobservado"].notna()
        & ~tabla["valorobservado"].between(*RANGO_OPERATIVO_C),
        "temperatura_fuera_rango_operativo",
    )
    _agregar_motivo(
        motivos,
        tabla["unidadmedida"].isna()
        | tabla["unidadmedida"].ne("°c").fillna(True),
        "unidad_no_celsius",
    )
    _agregar_motivo(
        motivos,
        ~tabla["descripcionsensor"].map(
            lambda valor: _descripcion_corresponde(valor, contrato["descripcion"])
        ),
        "descripcion_no_corresponde_variable",
    )
    _agregar_motivo(
        motivos,
        ~tabla["codigosensor"].isin(contrato["sensores"]),
        "sensor_fuera_contrato",
    )
    _agregar_motivo(
        motivos,
        tabla["dataset_id"].isna()
        | tabla["dataset_id"].str.lower().ne(spec.dataset_id).fillna(True),
        "fuente_fuera_particion",
    )
    _agregar_motivo(
        motivos,
        tabla["departamento"].isna()
        | tabla["departamento"].ne(spec.departamento).fillna(True),
        "departamento_fuera_particion",
    )

    fecha_valida = tabla["fechaobservacion"].notna()
    _agregar_motivo(
        motivos,
        fecha_valida & tabla["fechaobservacion"].dt.year.ne(spec.anio),
        "anio_fuera_particion",
    )
    _agregar_motivo(
        motivos,
        fecha_valida & tabla["fechaobservacion"].dt.month.ne(spec.mes),
        "mes_fuera_particion",
    )
    _agregar_motivo(
        motivos,
        tabla["latitud"].notna() & ~tabla["latitud"].between(-90, 90),
        "latitud_fuera_rango",
    )
    _agregar_motivo(
        motivos,
        tabla["longitud"].notna() & ~tabla["longitud"].between(-180, 180),
        "longitud_fuera_rango",
    )

    rechazados = tabla.loc[motivos.ne("")].copy()
    rechazados["motivo_rechazo"] = motivos.loc[motivos.ne("")]
    validos = tabla.loc[motivos.eq("")].copy()
    return validos.reset_index(drop=True), rechazados.reset_index(drop=True)


def depurar_claves(
    validos: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    if validos.empty:
        vacio = validos.copy()
        return vacio, vacio, vacio, {
            "filas_duplicadas_exactas_detectadas": 0,
            "filas_duplicadas_exactas_eliminadas": 0,
            "filas_clave_repetida_eliminadas": 0,
            "claves_conflictivas": 0,
            "filas_conflictivas_excluidas": 0,
        }

    columnas_exactas = list(COLUMNAS_REQUERIDAS)
    mascara_exacta = validos.duplicated(subset=columnas_exactas, keep=False)
    mascara_eliminar_exacta = validos.duplicated(subset=columnas_exactas, keep="first")
    duplicados_exactos = validos.loc[mascara_eliminar_exacta].copy()
    duplicados_exactos["tipo_duplicado"] = "exacto"
    unicos_exactos = validos.loc[~mascara_eliminar_exacta].copy()

    resumen_claves = (
        unicos_exactos.groupby(list(CLAVE_OBSERVACION), dropna=False)
        .agg(
            registros=("valorobservado", "size"),
            valores_distintos=("valorobservado", "nunique"),
        )
        .reset_index()
    )
    claves_conflictivas = resumen_claves.loc[
        resumen_claves["valores_distintos"] > 1,
        list(CLAVE_OBSERVACION),
    ]
    if claves_conflictivas.empty:
        conflictos = unicos_exactos.iloc[0:0].copy()
    else:
        conflictos = unicos_exactos.merge(
            claves_conflictivas.assign(_conflicto=True),
            on=list(CLAVE_OBSERVACION),
            how="inner",
        ).drop(columns="_conflicto")

    sin_conflictos = unicos_exactos.merge(
        claves_conflictivas.assign(_conflicto=True),
        on=list(CLAVE_OBSERVACION),
        how="left",
    )
    sin_conflictos = sin_conflictos.loc[
        sin_conflictos["_conflicto"].isna()
    ].drop(columns="_conflicto")
    mascara_clave_repetida = sin_conflictos.duplicated(
        subset=list(CLAVE_OBSERVACION), keep="first"
    )
    duplicados_clave = sin_conflictos.loc[mascara_clave_repetida].copy()
    duplicados_clave["tipo_duplicado"] = "clave_mismo_valor"
    depurados = sin_conflictos.loc[~mascara_clave_repetida].copy()

    duplicados = pd.concat([duplicados_exactos, duplicados_clave], ignore_index=True)
    metricas = {
        "filas_duplicadas_exactas_detectadas": int(mascara_exacta.sum()),
        "filas_duplicadas_exactas_eliminadas": len(duplicados_exactos),
        "filas_clave_repetida_eliminadas": len(duplicados_clave),
        "claves_conflictivas": len(claves_conflictivas),
        "filas_conflictivas_excluidas": len(conflictos),
    }
    return (
        depurados.sort_values("_orden_origen").reset_index(drop=True),
        conflictos.sort_values("_orden_origen").reset_index(drop=True),
        duplicados.sort_values("_orden_origen").reset_index(drop=True),
        metricas,
    )


def inferir_cadencias(depurados: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "codigoestacion",
        "codigosensor",
        "fecha",
        "intervalos_validos",
        "intervalo_moda_segundos",
        "intervalo_mediano_segundos",
        "intervalo_p10_segundos",
        "intervalo_p90_segundos",
        "cadencia_observada_conocida",
    ]
    if depurados.empty:
        return pd.DataFrame(columns=columnas)

    tiempos = depurados[
        ["codigoestacion", "codigosensor", "fechaobservacion"]
    ].drop_duplicates()
    tiempos = tiempos.sort_values(
        ["codigoestacion", "codigosensor", "fechaobservacion"]
    )
    tiempos["fecha"] = tiempos["fechaobservacion"].dt.floor("D")
    tiempos["delta_segundos"] = (
        tiempos.groupby(["codigoestacion", "codigosensor", "fecha"])[
            "fechaobservacion"
        ]
        .diff()
        .dt.total_seconds()
    )
    positivos = tiempos.loc[tiempos["delta_segundos"] > 0].copy()

    def moda(serie: pd.Series) -> float:
        modas = serie.mode()
        return float(modas.iloc[0]) if not modas.empty else float("nan")

    pares_dia = depurados[["codigoestacion", "codigosensor", "fechaobservacion"]].copy()
    pares_dia["fecha"] = pares_dia["fechaobservacion"].dt.floor("D")
    pares_dia = pares_dia[["codigoestacion", "codigosensor", "fecha"]].drop_duplicates()
    if positivos.empty:
        resumen = pd.DataFrame(columns=columnas[:-1])
    else:
        resumen = (
            positivos.groupby(
                ["codigoestacion", "codigosensor", "fecha"],
                as_index=False,
            )
            .agg(
                intervalos_validos=("delta_segundos", "size"),
                intervalo_moda_segundos=("delta_segundos", moda),
                intervalo_mediano_segundos=("delta_segundos", "median"),
                intervalo_p10_segundos=("delta_segundos", lambda s: s.quantile(0.10)),
                intervalo_p90_segundos=("delta_segundos", lambda s: s.quantile(0.90)),
            )
        )
    cadencias = pares_dia.merge(
        resumen,
        on=["codigoestacion", "codigosensor", "fecha"],
        how="left",
    )
    cadencias["cadencia_observada_conocida"] = cadencias[
        "intervalo_moda_segundos"
    ].isin(CADENCIAS_OBSERVADAS_SEGUNDOS)
    return cadencias[columnas]


def _unicos_texto(serie: pd.Series) -> str:
    valores = sorted({str(valor) for valor in serie.dropna()})
    return " | ".join(valores)


def agregar_diario(
    depurados: pd.DataFrame,
    cadencias: pd.DataFrame,
    duplicados: pd.DataFrame,
    conflictos: pd.DataFrame,
    spec: PartitionSpec,
) -> pd.DataFrame:
    if depurados.empty:
        return pd.DataFrame()

    contrato = _validar_contrato(spec)
    base = depurados.copy()
    base["fecha"] = base["fechaobservacion"].dt.floor("D")
    claves_dia = ["codigoestacion", "codigosensor", "fecha"]
    diario = (
        base.groupby(claves_dia, as_index=False, dropna=False)
        .agg(
            temperatura_media_observada_c=("valorobservado", "mean"),
            temperatura_mediana_observada_c=("valorobservado", "median"),
            temperatura_minima_observada_c=("valorobservado", "min"),
            temperatura_maxima_observada_c=("valorobservado", "max"),
            desviacion_estandar_observada_c=("valorobservado", "std"),
            observaciones_validas=("valorobservado", "size"),
            primera_observacion=("fechaobservacion", "min"),
            ultima_observacion=("fechaobservacion", "max"),
            municipios_observados=("municipio", _unicos_texto),
            nombres_estacion_observados=("nombreestacion", _unicos_texto),
            latitud_mediana=("latitud", "median"),
            longitud_mediana=("longitud", "median"),
        )
    )
    diario["amplitud_termica_observada_c"] = (
        diario["temperatura_maxima_observada_c"]
        - diario["temperatura_minima_observada_c"]
    )
    columna_principal = {
        "MEDIA": "temperatura_media_observada_c",
        "MINIMO": "temperatura_minima_observada_c",
        "MAXIMO": "temperatura_maxima_observada_c",
    }[contrato["estadistico_principal"]]
    diario["temperatura_principal_observada_c"] = diario[columna_principal]
    diario["estadistico_temperatura"] = contrato["estadistico_principal"]

    diario = diario.merge(
        cadencias,
        on=["codigoestacion", "codigosensor", "fecha"],
        how="left",
    )
    diario["cobertura_evaluable"] = (
        diario["cadencia_observada_conocida"].fillna(False).astype(bool)
    )
    diario["observaciones_esperadas"] = (
        86_400 / diario["intervalo_moda_segundos"]
    ).where(diario["cobertura_evaluable"])
    diario["cobertura_observada_pct"] = (
        100 * diario["observaciones_validas"] / diario["observaciones_esperadas"]
    ).round(2).where(diario["cobertura_evaluable"])
    diario["temperatura_diaria_c"] = pd.Series(
        pd.NA,
        index=diario.index,
        dtype="Float64",
    )
    diario["calidad_dia"] = "PENDIENTE_REGLA_COBERTURA"

    for nombre, tabla in (
        ("duplicados_eliminados", duplicados),
        ("conflictos_excluidos", conflictos),
    ):
        if tabla.empty:
            diario[nombre] = 0
            continue
        conteo = tabla.copy()
        conteo["fecha"] = conteo["fechaobservacion"].dt.floor("D")
        conteo = conteo.groupby(claves_dia).size().reset_index(name=nombre)
        diario = diario.merge(conteo, on=claves_dia, how="left")
        diario[nombre] = diario[nombre].fillna(0).astype(int)

    diario.insert(0, "variable", spec.variable)
    diario.insert(1, "dataset_id", spec.dataset_id)
    diario.insert(2, "departamento", spec.departamento)
    diario["regla_version"] = RULE_VERSION
    return diario.sort_values(claves_dia).reset_index(drop=True)


def procesar_temperatura(
    crudo: pd.DataFrame,
    spec: PartitionSpec,
) -> TemperatureProcessingResult:
    contrato = _validar_contrato(spec)
    validos, rechazados = preparar_observaciones(crudo, spec)
    depurados, conflictos, duplicados, metricas_depurar = depurar_claves(validos)
    cadencias = inferir_cadencias(depurados)
    diario = agregar_diario(depurados, cadencias, duplicados, conflictos, spec)

    metricas = {
        "regla_version": RULE_VERSION,
        "estadistico_principal": contrato["estadistico_principal"],
        "filas_entrada": len(crudo),
        "filas_validas_pre_deduplicacion": len(validos),
        "filas_rechazadas": len(rechazados),
        **metricas_depurar,
        "filas_validas_agregadas": len(depurados),
        "filas_diarias_salida": len(diario),
        "pares_estacion_sensor": int(
            depurados[["codigoestacion", "codigosensor"]].drop_duplicates().shape[0]
        ),
        "dias_distintos": int(diario["fecha"].nunique()) if not diario.empty else 0,
    }
    return TemperatureProcessingResult(
        diario=diario,
        cadencias=cadencias,
        rechazados=rechazados,
        conflictos=conflictos,
        duplicados_eliminados=duplicados,
        metricas=metricas,
    )
