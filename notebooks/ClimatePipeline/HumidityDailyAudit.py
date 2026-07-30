"""Marcador preventivo para la futura auditoria diaria de humedad."""

from __future__ import annotations

from typing import NoReturn


VARIABLE_NAME = "humedad"
DATASET_ID = "uext-mhny"
AUDIT_STATUS = "PENDIENTE_EVIDENCIA_DIARIA_Y_CONTRATO"


def detener_auditoria_pendiente() -> NoReturn:
    mensaje = (
        "⚠️ La auditoría diaria de humedad todavía no está implementada. "
        "Complete y revise un piloto del paso 03; luego defina cobertura, rangos, "
        "continuidad y tratamiento de sensores antes de habilitarla en 04."
    )
    print(mensaje)
    raise NotImplementedError(mensaje)


def auditar_humedad_diaria(*_args, **_kwargs) -> NoReturn:
    detener_auditoria_pendiente()
