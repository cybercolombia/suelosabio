"""Marcador preventivo para la futura auditoria diaria de velocidad del viento."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "velocidad_viento"
DATASET_ID = "sgfv-3yp8"
AUDIT_STATUS = "PENDIENTE_EVIDENCIA_DIARIA_Y_CONTRATO"


def detener_auditoria_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ La auditoría diaria de velocidad del viento todavía no está implementada. "
        "Complete y revise un piloto del paso 03; luego defina cobertura, calma, "
        "ráfagas, continuidad y sensores antes de habilitarla en 04."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def auditar_velocidad_viento_diaria(*_args, **_kwargs) -> NoReturn:
    detener_auditoria_pendiente()
