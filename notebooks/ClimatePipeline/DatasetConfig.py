"""Configuración compartida de ubicaciones de datasets para notebooks.

Este módulo es la única fuente de verdad para las raíces de datos del pipeline.
Detecta automáticamente Colab, puede montar Google Drive y permite sobrescribir
las rutas mediante variables de entorno sin editar los notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable


COLAB_SHARED_ROOT = Path("/content/drive/MyDrive/eco2026")
COLAB_PROCESSED_ROOT = Path("/content/drive/MyDrive/eco2026_processed")

LOCAL_PROCESSED_ROOT = Path(
    "/Users/eshernan/Library/CloudStorage/"
    "GoogleDrive-eshernan@gmail.com/.shortcut-targets-by-id/"
    "1aKoa_whG2LeZ05qCPObUHWR0-xZ95Qn7/eco2026_processed"
)
LOCAL_SHARED_ROOT = Path(
    "/Users/eshernan/Library/CloudStorage/"
    "GoogleDrive-eshernan@gmail.com/My Drive/eco2026"
)

SHARED_ROOT_ENV = "SUELOSABIO_SHARED_ROOT"
PROCESSED_ROOT_ENV = "SUELOSABIO_PROCESSED_ROOT"


@dataclass(frozen=True)
class DatasetConfig:
    """Rutas resueltas para el entorno actual."""

    in_colab: bool
    shared_root: Path
    processed_root: Path

    @property
    def climate_raw_root(self) -> Path:
        return self.processed_root / "clima_crudo"

    @property
    def eva_raw_root(self) -> Path:
        return self.processed_root / "eva_cruda"

    @property
    def geography_source_root(self) -> Path:
        """Directorio compartido con los catálogos y polígonos oficiales."""
        return self.shared_root

    @property
    def canonical_geography_root(self) -> Path:
        """Ruta histórica de precipitación; conservar por compatibilidad."""
        return self.canonical_geography_root_for("precipitacion")

    def canonical_geography_root_for(self, variable: str) -> Path:
        """Geografía canónica independiente para cada variable climática."""
        slug = str(variable).strip().lower()
        permitidos = set("abcdefghijklmnopqrstuvwxyz0123456789_")
        if not slug or any(char not in permitidos for char in slug):
            raise ValueError(f"Nombre de variable climática inválido: {variable!r}.")
        return (
            self.processed_root
            / "geografia_curada"
            / f"canonica=estaciones_{slug}_2024_2025_v3"
        )


def detectar_colab() -> bool:
    """Indica si el proceso se ejecuta dentro de Google Colab."""
    try:
        import google.colab  # noqa: F401
    except ImportError:
        return False
    return True


def _ruta_override(nombre: str, predeterminada: Path) -> Path:
    valor = os.environ.get(nombre)
    return Path(valor).expanduser() if valor else predeterminada


def _montar_drive() -> None:
    from google.colab import drive

    drive.mount("/content/drive")


def cargar_configuracion_datasets(
    *,
    in_colab: bool | None = None,
    montar_drive: bool = True,
    crear_processed_root: bool = False,
    drive_mounter: Callable[[], None] | None = None,
) -> DatasetConfig:
    """Resuelve las rutas compartidas para Colab o ejecución local.

    ``SUELOSABIO_SHARED_ROOT`` y ``SUELOSABIO_PROCESSED_ROOT`` permiten
    sobrescribir las rutas sin cambiar código. ``drive_mounter`` existe para
    probar el montaje sin depender de Colab.
    """

    modo_colab = detectar_colab() if in_colab is None else bool(in_colab)
    if modo_colab and montar_drive:
        (drive_mounter or _montar_drive)()

    shared_default = COLAB_SHARED_ROOT if modo_colab else LOCAL_SHARED_ROOT
    processed_default = COLAB_PROCESSED_ROOT if modo_colab else LOCAL_PROCESSED_ROOT
    configuracion = DatasetConfig(
        in_colab=modo_colab,
        shared_root=_ruta_override(SHARED_ROOT_ENV, shared_default),
        processed_root=_ruta_override(PROCESSED_ROOT_ENV, processed_default),
    )

    if crear_processed_root:
        configuracion.processed_root.mkdir(parents=True, exist_ok=True)

    return configuracion
