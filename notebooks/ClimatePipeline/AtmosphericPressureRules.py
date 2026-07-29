"""Marcador preventivo para el futuro contrato diario de presion."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "presion_atmosferica"
DATASET_ID = "62tk-nxj5"
RULE_STATUS = "PENDIENTE_AUDITORIA_Y_CONTRATO"


def detener_contrato_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ Presión atmosférica todavía no tiene reglas diarias aprobadas. "
        "Revise la auditoría 02, defina agregación, cobertura, rangos, altitud "
        "y sensores, y agregue pruebas antes de habilitarla en 03."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def procesar_presion_atmosferica(*_args, **_kwargs) -> NoReturn:
    detener_contrato_pendiente()

