"""Marcador preventivo para la futura auditoria diaria de presion."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "presion_atmosferica"
DATASET_ID = "62tk-nxj5"
AUDIT_STATUS = "PENDIENTE_EVIDENCIA_DIARIA_Y_CONTRATO"


def detener_auditoria_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ La auditoría diaria de presión atmosférica todavía no está implementada. "
        "Complete y revise un piloto del paso 03; luego defina cobertura, rangos, "
        "efecto de altitud, continuidad y sensores antes de habilitarla en 04."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def auditar_presion_atmosferica_diaria(*_args, **_kwargs) -> NoReturn:
    detener_auditoria_pendiente()
