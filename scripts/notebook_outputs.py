#!/usr/bin/env python3
"""Detecta o elimina estado de ejecución guardado en notebooks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {
    ".git",
    ".ipynb_checkpoints",
    ".tox",
    ".venv",
    "__pycache__",
}


def discover_notebooks(root: Path = REPOSITORY_ROOT) -> list[Path]:
    """Encuentra notebooks del repositorio sin recorrer entornos o caches."""
    return sorted(
        path
        for path in root.rglob("*.ipynb")
        if not IGNORED_DIRECTORIES.intersection(path.relative_to(root).parts)
    )


def execution_state(notebook: dict) -> list[str]:
    """Describe las salidas, contadores y widgets persistidos."""
    issues: list[str] = []
    for index, cell in enumerate(notebook.get("cells", []), start=1):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            issues.append(f"celda {index}: outputs")
        if cell.get("execution_count") is not None:
            issues.append(f"celda {index}: execution_count")
    if "widgets" in notebook.get("metadata", {}):
        issues.append("metadata: widgets")
    return issues


def clear_execution_state(notebook: dict) -> bool:
    """Elimina estado de ejecución y reporta si hubo modificaciones."""
    changed = False
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        if cell.get("outputs"):
            cell["outputs"] = []
            changed = True
        if cell.get("execution_count") is not None:
            cell["execution_count"] = None
            changed = True
    metadata = notebook.get("metadata", {})
    if "widgets" in metadata:
        metadata.pop("widgets")
        changed = True
    return changed


def process_notebooks(paths: Iterable[Path], *, fix: bool) -> tuple[int, int, int]:
    """Devuelve cantidades revisadas, con estado de ejecución y con errores."""
    reviewed = 0
    affected = 0
    errors = 0
    for path in paths:
        reviewed += 1
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors += 1
            print(f"ERROR {path}: no se pudo leer como notebook JSON ({exc})")
            continue

        issues = execution_state(notebook)
        if not issues:
            continue
        affected += 1
        if fix:
            clear_execution_state(notebook)
            path.write_text(
                json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8",
            )
            print(f"LIMPIADO {path}: {', '.join(issues)}")
        else:
            print(f"CON SALIDAS {path}: {', '.join(issues)}")
    return reviewed, affected, errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verifica o limpia outputs y contadores de notebooks."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Elimina el estado de ejecución en lugar de solo reportarlo.",
    )
    parser.add_argument("paths", nargs="*", type=Path, help="Notebooks a revisar.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = args.paths or discover_notebooks()
    missing = [path for path in paths if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR {path}: el archivo no existe.")
        return 2
    reviewed, affected, errors = process_notebooks(paths, fix=args.fix)
    action = "limpiados" if args.fix else "con estado de ejecución"
    print(
        f"Notebooks revisados: {reviewed}; {action}: {affected}; "
        f"errores: {errors}."
    )
    if errors:
        return 2
    return 0 if args.fix or affected == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
