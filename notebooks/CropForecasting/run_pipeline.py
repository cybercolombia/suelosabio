"""Ejecutor reproducible del dataset, backtesting y pronóstico 2026."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from urllib.request import urlopen

import joblib
import pandas as pd

from .climate import (
    CLIMATE_END,
    CLIMATE_START,
    aggregate_asof_semester_indicators,
    aggregate_semester_indicators,
    build_asof_climate_scenario,
    download_power_cells,
    municipality_grid,
    read_power_daily,
)
from .config import (
    EVA_DOWNLOAD_URL,
    FORECAST_AS_OF_DATE,
    FORECAST_VERSION,
    NASA_VERSION,
    load_forecasting_config,
)
from .dataset import build_definitive_dataset
from .eva import (
    build_potato_municipal_eva,
    read_upra_eva,
    select_target_municipalities,
    sha256_file,
)
from .modeling import metric_breakdown, run_temporal_backtesting


def download_eva_if_missing(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1_000_000:
        return target
    temporary = target.with_suffix(".xlsx.tmp")
    with urlopen(EVA_DOWNLOAD_URL, timeout=180) as response, temporary.open("wb") as out:
        shutil.copyfileobj(response, out)
    temporary.replace(target)
    return target


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def build_all(*, in_colab: bool | None = None) -> dict[str, object]:
    config = load_forecasting_config(
        in_colab=in_colab, mount_drive=True, create_outputs=True
    )
    eva_path = download_eva_if_missing(config.eva_source)
    raw_eva = read_upra_eva(eva_path)
    potato, eva_issues = build_potato_municipal_eva(raw_eva)
    targets = select_target_municipalities(potato)

    cells = municipality_grid(config.municipality_geography)
    potato_codes = set(potato["codigo_municipio"].astype(str))
    relevant_cells = cells[cells["codigo_municipio"].isin(potato_codes)].copy()
    cache_paths = download_power_cells(
        relevant_cells,
        config.nasa_raw_root,
        start=CLIMATE_START,
        end=CLIMATE_END,
    )
    daily = read_power_daily(relevant_cells, cache_paths)
    historical_daily = daily[daily["fecha"].dt.year.le(2025)].copy()
    historical_indicators = aggregate_semester_indicators(historical_daily)

    scenario_frames = []
    for year in range(2021, 2027):
        scenario_daily = build_asof_climate_scenario(daily, year)
        scenario_frames.append(aggregate_asof_semester_indicators(scenario_daily))
    scenarios = pd.concat(scenario_frames, ignore_index=True)
    forecast_climate = scenarios[scenarios["anio"].eq(2026)].copy()

    definitive = build_definitive_dataset(
        potato,
        targets,
        relevant_cells,
        historical_indicators,
        forecast_climate,
    )
    dataset_root = config.dataset_root
    definitive.dataset.to_parquet(dataset_root / "dataset_definitivo.parquet", index=False)
    definitive.target_municipalities.to_parquet(
        dataset_root / "municipios_objetivo.parquet", index=False
    )
    historical_indicators.to_parquet(
        dataset_root / "indicadores_climaticos_observados.parquet", index=False
    )
    scenarios.to_parquet(
        dataset_root / "escenarios_climaticos_asof.parquet", index=False
    )
    definitive.summary.to_parquet(
        dataset_root / "resumen_dataset.parquet", index=False
    )
    eva_issues.to_parquet(dataset_root / "incidencias_eva.parquet", index=False)
    dictionary = f"""# Diccionario del dataset definitivo

**Versión:** `{FORECAST_VERSION}`

- Llave: `codigo_municipio + anio + tipo_periodo + cultivo`.
- Target: `rendimiento_t_ha`.
- Horizonte: semestres A y B de 2026.
- `rendimiento_lag_*`: rendimientos conocidos de años anteriores.
- `area_sembrada_lag_*`: área sembrada histórica; no usa área 2026.
- Indicadores climáticos 2026-A: observados.
- Indicadores climáticos 2026-B: observados hasta {FORECAST_AS_OF_DATE} y
  climatología diaria 2019-2025 para las fechas posteriores.
- Columnas excluidas del modelado: producción y área cosechada, porque forman
  directamente el target.
"""
    (dataset_root / "data_dictionary.md").write_text(dictionary, encoding="utf-8")
    _write_json(
        dataset_root / "manifest.json",
        {
            "version": FORECAST_VERSION,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "forecast_as_of_date": FORECAST_AS_OF_DATE,
            "eva_source": str(eva_path),
            "eva_sha256": sha256_file(eva_path),
            "nasa_version": NASA_VERSION,
            "nasa_start": CLIMATE_START,
            "nasa_end": CLIMATE_END,
            "nasa_cached_cells": len(cache_paths),
            "rows": len(definitive.dataset),
            "target_municipalities": len(targets),
            "climate_features": list(definitive.climate_feature_columns),
            "status": "COMPLETE",
        },
    )

    evaluation = run_temporal_backtesting(
        definitive.dataset,
        scenarios,
        definitive.climate_feature_columns,
    )
    model_root = config.model_root
    evaluation.leaderboard.to_csv(model_root / "leaderboard.csv", index=False)
    evaluation.fold_metrics.to_csv(model_root / "metricas_por_fold.csv", index=False)
    evaluation.backtest_predictions.to_parquet(
        model_root / "predicciones_backtest.parquet", index=False
    )
    breakdown = metric_breakdown(evaluation.backtest_predictions)
    breakdown.to_csv(model_root / "metricas_desagregadas.csv", index=False)
    evaluation.forecast_2026.to_parquet(
        model_root / "pronostico_2026.parquet", index=False
    )
    evaluation.forecast_2026.to_csv(
        model_root / "pronostico_2026.csv", index=False
    )
    if evaluation.final_estimator is not None:
        joblib.dump(evaluation.final_estimator, model_root / "modelo_final.joblib")
    _write_json(
        model_root / "manifest.json",
        {
            "version": FORECAST_VERSION,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "selected_model": evaluation.selected_model,
            "selected_encoding": evaluation.selected_encoding,
            "selection_metric": "MAE promedio 2024-2025",
            "backtest_years": [2021, 2022, 2023, 2024, 2025],
            "forecast_rows": len(evaluation.forecast_2026),
            "status": "COMPLETE",
        },
    )
    return {
        "config": config,
        "dataset": definitive,
        "scenarios": scenarios,
        "evaluation": evaluation,
        "breakdown": breakdown,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--colab",
        action="store_true",
        help="Fuerza configuración Colab y montaje de Google Drive.",
    )
    args = parser.parse_args()
    result = build_all(in_colab=True if args.colab else False)
    evaluation = result["evaluation"]
    print(f"Modelo seleccionado: {evaluation.selected_model}")
    print(f"Representación: {evaluation.selected_encoding}")
    print(evaluation.leaderboard.head(5).to_string(index=False))
    print(f"Pronósticos 2026: {len(evaluation.forecast_2026)}")


if __name__ == "__main__":
    main()
