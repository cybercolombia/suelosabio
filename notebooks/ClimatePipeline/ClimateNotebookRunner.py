"""Ejecutor explícito de notebooks del pipeline sin depender de Jupyter.

Solo habilita las banderas indicadas por línea de comandos. Es útil para
reanudar etapas incrementales desde terminal o Colab y conserva las banderas
de seguridad en el archivo original.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


def ejecutar_notebook(
    ruta: str | Path,
    *,
    habilitar: list[str] | tuple[str, ...],
    valores: dict[str, Any] | None = None,
) -> dict[str, Any]:
    notebook_path = Path(ruta).resolve()
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    namespace: dict[str, Any] = {
        "__name__": "__climate_notebook_runner__",
        "__file__": str(notebook_path),
    }
    pendientes = set(habilitar)
    valores = valores or {}
    valores_pendientes = set(valores)
    for indice, celda in enumerate(notebook.get("cells", [])):
        if celda.get("cell_type") != "code":
            continue
        codigo = "".join(celda.get("source", []))
        for bandera in habilitar:
            patron = rf"(?m)^{re.escape(bandera)}\s*=\s*False\b"
            codigo, cambios = re.subn(
                patron,
                f"{bandera} = True",
                codigo,
            )
            if cambios:
                pendientes.discard(bandera)
        for nombre, valor in valores.items():
            patron = rf"(?m)^{re.escape(nombre)}\s*=.*$"
            codigo, cambios = re.subn(
                patron,
                f"{nombre} = {valor!r}",
                codigo,
                count=1,
            )
            if cambios:
                valores_pendientes.discard(nombre)
        exec(
            compile(
                codigo,
                f"{notebook_path.name}:cell_{indice}",
                "exec",
            ),
            namespace,
        )
    if pendientes:
        raise ValueError(
            "No se encontraron estas banderas en el notebook: "
            f"{sorted(pendientes)}."
        )
    if valores_pendientes:
        raise ValueError(
            "No se encontraron estas configuraciones en el notebook: "
            f"{sorted(valores_pendientes)}."
        )
    return namespace


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("notebook", type=Path)
    parser.add_argument(
        "--enable",
        action="append",
        required=True,
        help="Nombre exacto de una bandera booleana que debe habilitarse.",
    )
    parser.add_argument(
        "--set-json",
        action="append",
        default=[],
        metavar="NOMBRE=JSON",
        help="Sobrescribe una asignación simple sin modificar el notebook.",
    )
    argumentos = parser.parse_args()
    valores = {}
    for asignacion in argumentos.set_json:
        nombre, separador, contenido = asignacion.partition("=")
        if not separador or not nombre.isidentifier():
            raise ValueError(f"Asignación inválida: {asignacion!r}.")
        valores[nombre] = json.loads(contenido)
    ejecutar_notebook(
        argumentos.notebook,
        habilitar=argumentos.enable,
        valores=valores,
    )


if __name__ == "__main__":
    main()
