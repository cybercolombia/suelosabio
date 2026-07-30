"""Auditoría diaria reutilizable para variables meteorológicas escalares."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from TemperatureDailyAudit import auditar_temperatura_diaria


AUDIT_VERSION = "auditoria_escalar_diaria_v1"
_TO_TEMPERATURE = {
    "valor_principal_observado": "temperatura_principal_observada_c",
    "valor_medio_observado": "temperatura_media_observada_c",
    "valor_mediano_observado": "temperatura_mediana_observada_c",
    "valor_minimo_observado": "temperatura_minima_observada_c",
    "valor_maximo_observado": "temperatura_maxima_observada_c",
    "amplitud_observada": "amplitud_termica_observada_c",
    "valor_diario": "temperatura_diaria_c",
}
_REASON_REPLACEMENTS = {
    "TEMPERATURA_MUY_BAJA": "VALOR_MUY_BAJO",
    "TEMPERATURA_MUY_ALTA": "VALOR_MUY_ALTO",
    "AMPLITUD_TERMICA_ALTA": "AMPLITUD_DIARIA_ALTA",
}


@dataclass(slots=True)
class DailyScalarAuditResult:
    calendario: pd.DataFrame
    resumen_particiones: pd.DataFrame
    resumen_pares: pd.DataFrame
    valores_sospechosos: pd.DataFrame
    comparaciones_sensores: pd.DataFrame
    resumen_sensores_paralelos: pd.DataFrame
    metricas: dict[str, Any]


def _restore(table: pd.DataFrame) -> pd.DataFrame:
    replacements = {
        target: source for source, target in _TO_TEMPERATURE.items()
    }
    replacements.update(
        {
            "temperatura_principal_min_c": "valor_principal_minimo",
            "temperatura_principal_mediana_c": "valor_principal_mediano",
            "temperatura_principal_max_c": "valor_principal_maximo",
        }
    )
    restored = table.rename(
        columns=lambda column: next(
            (
                str(column).replace(target, source)
                for target, source in replacements.items()
                if target in str(column)
            ),
            column,
        )
    )
    for column in restored.select_dtypes(include=["object", "string"]).columns:
        restored[column] = restored[column].replace(
            _REASON_REPLACEMENTS, regex=True
        )
    return restored


def auditar_escalar_diario(
    diario: pd.DataFrame,
    *,
    umbral_minimo: float,
    umbral_maximo: float,
    umbral_amplitud: float,
    tolerancia_sensores: float,
    umbral_cobertura_pct: float = 90.0,
    tolerancia_cobertura_superior_pct: float = 102.0,
) -> DailyScalarAuditResult:
    adapted = diario.rename(columns=_TO_TEMPERATURE)
    result = auditar_temperatura_diaria(
        adapted,
        umbral_cobertura_pct=umbral_cobertura_pct,
        tolerancia_cobertura_superior_pct=tolerancia_cobertura_superior_pct,
        umbral_minimo_c=umbral_minimo,
        umbral_maximo_c=umbral_maximo,
        umbral_amplitud_c=umbral_amplitud,
        tolerancia_sensores_c=tolerancia_sensores,
    )
    metrics = {
        **result.metricas,
        "audit_version": AUDIT_VERSION,
        "umbral_minimo": float(umbral_minimo),
        "umbral_maximo": float(umbral_maximo),
        "umbral_amplitud": float(umbral_amplitud),
        "tolerancia_sensores": float(tolerancia_sensores),
    }
    for key in (
        "umbral_minimo_c",
        "umbral_maximo_c",
        "umbral_amplitud_c",
        "tolerancia_sensores_c",
    ):
        metrics.pop(key, None)
    return DailyScalarAuditResult(
        calendario=_restore(result.calendario),
        resumen_particiones=_restore(result.resumen_particiones),
        resumen_pares=_restore(result.resumen_pares),
        valores_sospechosos=_restore(result.valores_sospechosos),
        comparaciones_sensores=_restore(result.comparaciones_sensores),
        resumen_sensores_paralelos=_restore(result.resumen_sensores_paralelos),
        metricas=metrics,
    )
