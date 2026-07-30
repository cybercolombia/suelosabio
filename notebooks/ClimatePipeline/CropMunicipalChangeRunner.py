"""Corrida incremental del agregado agrícola municipal y su auditoría espacial."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import geopandas as gpd
import pandas as pd

from ClimateProcessingUtils import (
    escribir_json_atomico,
    escribir_parquet_atomico,
    escribir_texto_atomico,
)
from CropMunicipalChange import (
    AGGREGATION_VERSION,
    CHANGE_VERSION,
    GEOGRAPHY_VERSION,
    aggregate_crop_municipal_period,
    audit_crop_geography,
)
from DatasetConfig import DatasetConfig


def _input_signature(files: list[Path], geography: Path) -> dict[str, object]:
    inputs = [*files, geography]
    return {
        "archivos": len(files),
        "bytes": sum(path.stat().st_size for path in inputs),
        "mtime_ns_maximo": max(path.stat().st_mtime_ns for path in inputs),
    }


def _can_reuse(manifest: Path, signature: dict[str, object]) -> bool:
    if not manifest.exists():
        return False
    content = json.loads(manifest.read_text(encoding="utf-8"))
    return (
        content.get("estado", "").startswith("COMPLETA")
        and content.get("aggregation_version") == AGGREGATION_VERSION
        and content.get("firma_entrada") == signature
    )


def run_crop_municipal_change(
    config: DatasetConfig,
    *,
    dataset_id: str = "uejq-wxrr",
    overwrite: bool = False,
    progress: Callable[[str], None] = print,
) -> dict[str, object]:
    raw_root = config.eva_raw_root / f"fuente={dataset_id}"
    files = sorted(raw_root.rglob("part-*.parquet"))
    if not files:
        raise FileNotFoundError(f"No hay particiones EVA en {raw_root}")
    geography_path = (
        config.canonical_geography_root / "divipola_municipios_geometria.parquet"
    )
    if not geography_path.exists():
        raise FileNotFoundError(f"No existe la geografía canónica: {geography_path}")

    output = (
        config.processed_root
        / "agricultura_municipal"
        / f"version={AGGREGATION_VERSION}"
    )
    manifest = output / "manifest.json"
    signature = _input_signature(files, geography_path)
    if _can_reuse(manifest, signature) and not overwrite:
        progress("Agregado agrícola municipal completo y vigente; se reutiliza.")
        return {"output": output, "manifest": manifest, "reused": True}
    if manifest.exists() and not overwrite:
        raise RuntimeError(
            "Existe una corrida con entradas distintas. Use overwrite=True para "
            "publicar una nueva materialización de esta versión."
        )

    blocks = []
    total = 0
    for index, path in enumerate(files, start=1):
        block = pd.read_parquet(path)
        blocks.append(block)
        total += len(block)
        progress(
            f"[{index}/{len(files)}] {path.parent.name}: "
            f"{len(block):,} filas; total={total:,}"
        )
    raw = pd.concat(blocks, ignore_index=True)
    result = aggregate_crop_municipal_period(raw)
    geography = gpd.read_parquet(geography_path)
    geo_audit = audit_crop_geography(result.municipal_period, geography)

    tables = {
        "cultivo_municipio_periodo.parquet": result.municipal_period,
        "cambios_interanuales.parquet": result.changes,
        "incidencias_agregacion.parquet": result.issues,
        "resumen_agregacion.parquet": result.summary,
        "auditoria_geografica.parquet": geo_audit.summary,
        "cultivos_sin_geometria.parquet": geo_audit.crop_without_geometry,
        "geometrias_sin_cultivo.parquet": geo_audit.geometry_without_crop,
        "diferencias_nombres_divipola.parquet": geo_audit.name_differences,
    }
    for name, table in tables.items():
        escribir_parquet_atomico(table, output / name, overwrite)

    summary = result.summary.iloc[0].to_dict()
    geo_summary = geo_audit.summary.iloc[0].to_dict()
    report = (
        "# Auditoría del agregado cultivo–municipio–período\n\n"
        f"- Filas EVA: {summary['filas_entrada']:,}\n"
        f"- Filas utilizables: {summary['filas_utilizables']:,}\n"
        f"- Targets municipales: {summary['targets_municipio_periodo']:,}\n"
        f"- Comparaciones interanuales: {summary['filas_cambio_interanual']:,}\n"
        f"- Municipios sin geometría: {geo_summary['municipios_sin_geometria']}\n"
        f"- Estado agregado: `{summary['estado']}`\n"
        f"- Estado geográfico: `{geo_summary['estado']}`\n"
    )
    escribir_texto_atomico(report, output / "AuditoriaAgregadoMunicipal.md", overwrite)
    escribir_json_atomico(
        {
            "estado": summary["estado"],
            "aggregation_version": AGGREGATION_VERSION,
            "change_version": CHANGE_VERSION,
            "geography_version": GEOGRAPHY_VERSION,
            "dataset_id": dataset_id,
            "firma_entrada": signature,
            "geografia_entrada": str(geography_path),
            **summary,
            "estado_geografico": geo_summary["estado"],
            "municipios_sin_geometria": geo_summary["municipios_sin_geometria"],
            "geometrias_sin_agricultura": geo_summary["geometrias_sin_agricultura"],
        },
        manifest,
        overwrite,
    )
    progress(
        f"Agregado completo: {len(result.municipal_period):,} targets y "
        f"{len(result.changes):,} comparaciones."
    )
    return {"output": output, "manifest": manifest, "reused": False}
