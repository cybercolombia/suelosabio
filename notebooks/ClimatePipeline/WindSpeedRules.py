"""Marcador preventivo para el futuro contrato diario de velocidad del viento."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "velocidad_viento"
DATASET_ID = "sgfv-3yp8"
RULE_STATUS = "PENDIENTE_AUDITORIA_Y_CONTRATO"


def detener_contrato_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ Velocidad del viento todavía no tiene reglas diarias aprobadas. "
        "Revise la auditoría 02, defina agregación, cobertura, calma, ráfagas y "
        "sensores, y agregue pruebas antes de habilitarla en 03."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def procesar_velocidad_viento(*_args, **_kwargs) -> NoReturn:
    detener_contrato_pendiente()

