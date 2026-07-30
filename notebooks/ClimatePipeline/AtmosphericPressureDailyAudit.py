"""Auditoría diaria de presión atmosférica."""

from ScalarDailyAudit import AUDIT_VERSION, auditar_escalar_diario

VARIABLE_NAME = "presion_atmosferica"
DATASET_ID = "62tk-nxj5"
AUDIT_STATUS = "IMPLEMENTADA_PILOTO_PENDIENTE"


def auditar_presion_atmosferica_diaria(diario, **kwargs):
    return auditar_escalar_diario(
        diario,
        umbral_minimo=500.0,
        umbral_maximo=1050.0,
        umbral_amplitud=100.0,
        tolerancia_sensores=2.0,
        **kwargs,
    )
