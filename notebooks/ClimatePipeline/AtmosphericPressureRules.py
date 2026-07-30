"""Contrato diario de presión atmosférica."""

from ScalarClimateRules import COLUMNAS_REQUERIDAS, RULE_VERSION, procesar_escalar


VARIABLE_NAME = "presion_atmosferica"
DATASET_ID = "62tk-nxj5"
RULE_STATUS = "IMPLEMENTADO_PILOTO_PENDIENTE"


def procesar_presion_atmosferica(crudo, spec):
    return procesar_escalar(crudo, spec)
