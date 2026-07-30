"""Contrato diario de velocidad del viento."""

from ScalarClimateRules import COLUMNAS_REQUERIDAS, RULE_VERSION, procesar_escalar


VARIABLE_NAME = "velocidad_viento"
DATASET_ID = "sgfv-3yp8"
RULE_STATUS = "IMPLEMENTADO_PILOTO_PENDIENTE"


def procesar_velocidad_viento(crudo, spec):
    return procesar_escalar(crudo, spec)
