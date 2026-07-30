"""Configuración única de entradas y artefactos de CropForecasting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from notebooks.ClimatePipeline.DatasetConfig import (
    DatasetConfig,
    cargar_configuracion_datasets,
)


EVA_FILENAME = "20260526_BaseAgricola20192025.xlsx"
EVA_DOWNLOAD_URL = (
    "https://upra.gov.co/sites/default/files/2026-05/"
    "20260526_BaseAgricola20192025.xlsx"
)
FORECAST_VERSION = "papa_rendimiento_2026_v1"
NASA_VERSION = "nasa_power_daily_2019_2026_07_30_v1"
FORECAST_AS_OF_DATE = "2026-07-30"


@dataclass(frozen=True)
class ForecastingConfig:
    """Rutas resueltas sin duplicar la lógica local/Colab del proyecto."""

    datasets: DatasetConfig

    @property
    def root(self) -> Path:
        return self.datasets.processed_root / "crop_forecasting"

    @property
    def eva_source(self) -> Path:
        return self.datasets.shared_root / EVA_FILENAME

    @property
    def municipality_geography(self) -> Path:
        return self.datasets.shared_root / "Boyaca_Cundinamarca_Municipios.gpkg"

    @property
    def nasa_raw_root(self) -> Path:
        return self.root / "raw" / "nasa_power" / f"version={NASA_VERSION}"

    @property
    def dataset_root(self) -> Path:
        return self.root / "datasets" / f"version={FORECAST_VERSION}"

    @property
    def model_root(self) -> Path:
        return self.root / "models" / f"version={FORECAST_VERSION}"

    def create_output_directories(self) -> None:
        for path in (self.nasa_raw_root, self.dataset_root, self.model_root):
            path.mkdir(parents=True, exist_ok=True)


def load_forecasting_config(
    *,
    in_colab: bool | None = None,
    mount_drive: bool = True,
    create_outputs: bool = False,
) -> ForecastingConfig:
    datasets = cargar_configuracion_datasets(
        in_colab=in_colab,
        montar_drive=mount_drive,
        crear_processed_root=create_outputs,
    )
    config = ForecastingConfig(datasets=datasets)
    if create_outputs:
        config.create_output_directories()
    return config
