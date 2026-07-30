"""Auditoría diaria de velocidad del viento."""

from ScalarDailyAudit import AUDIT_VERSION, auditar_escalar_diario

VARIABLE_NAME = "velocidad_viento"
DATASET_ID = "sgfv-3yp8"
AUDIT_STATUS = "IMPLEMENTADA_PILOTO_PENDIENTE"


def auditar_velocidad_viento_diaria(diario, **kwargs):
    return auditar_escalar_diario(
        diario,
        umbral_minimo=0.0,
        umbral_maximo=40.0,
        umbral_amplitud=30.0,
        tolerancia_sensores=1.0,
        **kwargs,
    )
