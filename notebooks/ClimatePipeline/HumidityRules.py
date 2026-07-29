"""Marcador preventivo para el futuro contrato diario de humedad."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "humedad"
DATASET_ID = "uext-mhny"
RULE_STATUS = "PENDIENTE_AUDITORIA_Y_CONTRATO"


def detener_contrato_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ Humedad todavía no tiene reglas diarias aprobadas. "
        "Revise la auditoría 02, defina agregación, cobertura, rangos y sensores, "
        "y agregue pruebas antes de habilitarla en 03."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def procesar_humedad(*_args, **_kwargs) -> NoReturn:
    detener_contrato_pendiente()

