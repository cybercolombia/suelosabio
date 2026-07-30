"""Ejecución reanudable por etapas del pipeline de auditoría EVA."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pandas as pd

from ClimateProcessingUtils import (
    escribir_json_atomico,
    escribir_parquet_atomico,
    escribir_texto_atomico,
)
from CropYieldProcessing import (
    AUDIT_VERSION,
    CURATED_AUDIT_VERSION,
    CURATION_VERSION,
    audit_curated_eva,
    audit_raw_eva,
    curate_eva,
)
from DatasetConfig import DatasetConfig


def _manifest_complete(path: Path, version_key: str, version: str) -> bool:
    if not path.exists():
        return False
    content = json.loads(path.read_text(encoding="utf-8"))
    return (
        str(content.get("estado", "")).startswith("COMPLETA")
        and content.get(version_key) == version
    )


def _read_incrementally(files: list[Path], progress: Callable[[str], None]) -> pd.DataFrame:
    blocks = []
    total = 0
    for index, path in enumerate(files, start=1):
        block = pd.read_parquet(path)
        blocks.append(block)
        total += len(block)
        progress(f"[{index}/{len(files)}] {path.parent.name}: {len(block):,} filas; total={total:,}")
    return pd.concat(blocks, ignore_index=True)


def run_crop_yield_audits(
    config: DatasetConfig,
    *,
    dataset_id: str = "uejq-wxrr",
    crops: list[str] | None = None,
    overwrite: bool = False,
    progress: Callable[[str], None] = print,
) -> dict[str, object]:
    raw_root = config.eva_raw_root / f"fuente={dataset_id}"
    files = sorted(raw_root.rglob("part-*.parquet"))
    if not files:
        raise FileNotFoundError(f"No hay archivos EVA en {raw_root}")

    raw_output = (
        config.processed_root
        / "auditorias_agricultura"
        / "capa=eva_cruda"
        / f"fuente={dataset_id}"
        / "auditoria=eva_cruda_2019_2025_v1"
    )
    curated_output = (
        config.processed_root / "agricultura_curada" / f"version={CURATION_VERSION}"
    )
    curated_audit_output = (
        config.processed_root
        / "auditorias_agricultura"
        / "capa=eva_curada"
        / f"auditoria={CURATED_AUDIT_VERSION}"
    )

    raw_manifest = raw_output / "manifest.json"
    if _manifest_complete(raw_manifest, "audit_version", AUDIT_VERSION) and not overwrite:
        progress("01/03 Auditoría cruda ya completa; se reutiliza.")
    else:
        progress("01/03 Leyendo particiones para auditoría cruda.")
        raw = _read_incrementally(files, progress)
        result = audit_raw_eva(raw)
        tables = {
            "resumen_auditoria.parquet": result.summary,
            "nulos_columnas.parquet": result.missingness,
            "llaves_duplicadas.parquet": result.duplicate_keys,
            "banderas_calidad.parquet": result.quality_flags,
            "cobertura_eva.parquet": result.coverage,
        }
        for name, table in tables.items():
            escribir_parquet_atomico(table, raw_output / name, overwrite)
        summary = result.summary.iloc[0].to_dict()
        escribir_texto_atomico(
            f"# Auditoría EVA cruda\n\nFilas: {summary['filas']:,}\n",
            raw_output / "AuditoriaEvaCruda.md",
            overwrite,
        )
        escribir_json_atomico(
            {
                "estado": "COMPLETA_CON_REVISION_PENDIENTE",
                "audit_version": AUDIT_VERSION,
                "dataset_id": dataset_id,
                "archivos_entrada": len(files),
                **summary,
            },
            raw_manifest,
            overwrite,
        )
        progress(f"01/03 Auditoría cruda completa: {len(raw):,} filas.")

    curated_manifest = curated_output / "manifest.json"
    if _manifest_complete(
        curated_manifest, "curation_version", CURATION_VERSION
    ) and not overwrite:
        progress("02/03 Curación ya completa; se reutiliza.")
    else:
        progress("02/03 Leyendo particiones para curación.")
        raw = _read_incrementally(files, progress)
        result = curate_eva(raw, crops=crops)
        for name, table in {
            "eva_curada.parquet": result.curated,
            "exclusiones.parquet": result.exclusions,
            "reconciliacion.parquet": result.reconciliation,
            "resumen_cobertura.parquet": result.summary,
        }.items():
            escribir_parquet_atomico(table, curated_output / name, overwrite)
        escribir_texto_atomico(
            "# Diccionario EVA curada\n\n"
            "`rendimiento_t_ha` es producción / área cosechada. "
            "Producción y área cosechada no son predictores.\n",
            curated_output / "data_dictionary.md",
            overwrite,
        )
        escribir_json_atomico(
            {
                "estado": "COMPLETA_CON_REVISION_PENDIENTE",
                "curation_version": CURATION_VERSION,
                "dataset_id": dataset_id,
                "cultivos_objetivo": crops,
                "filas_curadas": len(result.curated),
                "filas_excluidas": len(result.exclusions),
                "llave": ["codigo_municipio", "anio", "periodo", "cultivo"],
                "columnas_no_predictoras": ["produccion_t", "area_cosechada_ha"],
            },
            curated_manifest,
            overwrite,
        )
        progress(
            f"02/03 Curación completa: {len(result.curated):,} targets; "
            f"{len(result.exclusions):,} filas excluidas."
        )

    curated_audit_manifest = curated_audit_output / "manifest.json"
    if _manifest_complete(
        curated_audit_manifest, "audit_version", CURATED_AUDIT_VERSION
    ) and not overwrite:
        progress("03/03 Auditoría curada ya completa; se reutiliza.")
    else:
        progress("03/03 Auditando el producto curado.")
        curated = pd.read_parquet(curated_output / "eva_curada.parquet")
        audit = audit_curated_eva(curated)
        for name, table in audit.items():
            escribir_parquet_atomico(
                table, curated_audit_output / f"{name}.parquet", overwrite
            )
        summary = audit["summary"].iloc[0].to_dict()
        escribir_texto_atomico(
            f"# Auditoría EVA curada\n\nEstado: `{summary['estado']}`\n",
            curated_audit_output / "AuditoriaEvaCurada.md",
            overwrite,
        )
        escribir_json_atomico(
            {
                "curation_version": CURATION_VERSION,
                "audit_version": CURATED_AUDIT_VERSION,
                **summary,
            },
            curated_audit_manifest,
            overwrite,
        )
        progress(f"03/03 Auditoría curada terminada: {summary['estado']}.")

    return {
        "raw_manifest": raw_manifest,
        "curated_manifest": curated_manifest,
        "curated_audit_manifest": curated_audit_manifest,
        "files": len(files),
    }
