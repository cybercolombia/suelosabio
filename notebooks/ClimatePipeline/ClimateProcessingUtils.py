"""Utilidades compartidas por los notebooks del pipeline climatico."""

from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

import pandas as pd


DATASET_ID_PATTERN = re.compile(r"^[a-z0-9]{4}-[a-z0-9]{4}$", re.IGNORECASE)
PART_PATTERN = re.compile(r"^part-(\d{5})\.parquet$")
DEPARTAMENTOS_CANONICOS = {
    "boyaca": "BOYACÁ",
    "cundinamarca": "CUNDINAMARCA",
}
ZONA_HORARIA_PROYECTO = ZoneInfo("America/Bogota")


def normalizar_unicode(valor: Any) -> str:
    return unicodedata.normalize("NFC", str(valor).strip())


def slugificar(valor: Any) -> str:
    texto = unicodedata.normalize("NFKD", str(valor))
    texto = texto.encode("ascii", errors="ignore").decode("ascii").lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    if not texto:
        raise ValueError(f"No se pudo construir una etiqueta para {valor!r}.")
    return texto


def normalizar_departamento(valor: Any) -> str:
    clave = slugificar(normalizar_unicode(valor))
    if clave not in DEPARTAMENTOS_CANONICOS:
        raise ValueError(f"Departamento fuera del alcance: {valor}.")
    return DEPARTAMENTOS_CANONICOS[clave]


@dataclass(frozen=True, slots=True)
class PartitionSpec:
    variable: str
    dataset_id: str
    departamento: str
    anio: int
    mes: int

    def __post_init__(self) -> None:
        variable = slugificar(self.variable)
        dataset_id = normalizar_unicode(self.dataset_id).lower()
        departamento = normalizar_departamento(self.departamento)
        anio = int(self.anio)
        mes = int(self.mes)

        if not DATASET_ID_PATTERN.fullmatch(dataset_id):
            raise ValueError("dataset_id debe tener el formato xxxx-xxxx.")
        if anio < 1900 or anio > 2100:
            raise ValueError(f"Ano fuera de rango: {anio}.")
        if mes < 1 or mes > 12:
            raise ValueError(f"Mes fuera de rango: {mes}.")

        object.__setattr__(self, "variable", variable)
        object.__setattr__(self, "dataset_id", dataset_id)
        object.__setattr__(self, "departamento", departamento)
        object.__setattr__(self, "anio", anio)
        object.__setattr__(self, "mes", mes)

    def como_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def etiqueta(self) -> str:
        return (
            f"{self.variable}_{self.dataset_id}_{slugificar(self.departamento)}_"
            f"{self.anio}_{self.mes:02d}"
        )


def construir_plan_particiones(
    variable: str,
    dataset_id: str,
    departamentos: Iterable[str],
    anios: Iterable[int],
    meses: Iterable[int],
) -> list[PartitionSpec]:
    return [
        PartitionSpec(variable, dataset_id, departamento, anio, mes)
        for departamento in sorted(set(departamentos))
        for anio in sorted({int(valor) for valor in anios})
        for mes in sorted({int(valor) for valor in meses})
    ]


def _resolver_hijo_unicode(raiz: Path, nombre: str) -> Path:
    candidato = raiz / nombre
    if not raiz.exists():
        return candidato

    nombre_normalizado = normalizar_unicode(nombre)
    coincidencias = [
        ruta
        for ruta in raiz.iterdir()
        if ruta.is_dir() and normalizar_unicode(ruta.name) == nombre_normalizado
    ]
    if len(coincidencias) > 1:
        raise RuntimeError(
            f"Hay carpetas equivalentes por Unicode para {nombre}: {coincidencias}."
        )
    return coincidencias[0] if coincidencias else candidato


def ruta_particion_cruda(processed_root: Path, spec: PartitionSpec) -> Path:
    raiz_fuente = (
        Path(processed_root)
        / "clima_crudo"
        / f"variable={spec.variable}"
        / f"fuente={spec.dataset_id}"
    )
    departamento = _resolver_hijo_unicode(
        raiz_fuente,
        f"departamento={spec.departamento}",
    )
    return departamento / f"anio={spec.anio}" / f"mes={spec.mes:02d}"


def ruta_particion_diaria(processed_root: Path, spec: PartitionSpec) -> Path:
    return (
        Path(processed_root)
        / "clima_diario_sensor"
        / f"variable={spec.variable}"
        / f"fuente={spec.dataset_id}"
        / f"departamento={spec.departamento}"
        / f"anio={spec.anio}"
        / f"mes={spec.mes:02d}"
    )


def descubrir_partes_parquet(ruta: Path) -> list[Path]:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la particion cruda: {ruta}")

    partes = []
    for archivo in ruta.glob("part-*.parquet"):
        coincidencia = PART_PATTERN.fullmatch(archivo.name)
        if coincidencia:
            partes.append((int(coincidencia.group(1)), archivo))
    partes.sort(key=lambda item: item[0])
    if not partes:
        raise FileNotFoundError(f"No hay archivos part-*.parquet en {ruta}")

    indices = [indice for indice, _ in partes]
    esperados = list(range(indices[-1] + 1))
    if indices != esperados:
        faltantes = sorted(set(esperados) - set(indices))
        raise RuntimeError(f"La particion tiene partes faltantes: {faltantes}.")
    return [archivo for _, archivo in partes]


def inventariar_parquets(archivos: Sequence[Path]) -> pd.DataFrame:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise ImportError("Se necesita pyarrow para inspeccionar Parquet.") from exc

    filas = []
    for archivo in archivos:
        parquet = pq.ParquetFile(archivo)
        filas.append(
            {
                "archivo": str(archivo),
                "filas": parquet.metadata.num_rows,
                "columnas": parquet.schema_arrow.names,
                "tamano_bytes": archivo.stat().st_size,
            }
        )
    return pd.DataFrame(filas)


def leer_particion_parquet(
    archivos: Sequence[Path],
    columnas: Sequence[str] | None = None,
) -> pd.DataFrame:
    bloques = [pd.read_parquet(archivo, columns=columnas) for archivo in archivos]
    if not bloques:
        return pd.DataFrame(columns=list(columnas or []))
    return pd.concat(bloques, ignore_index=True)


def escribir_parquet_atomico(
    tabla: pd.DataFrame,
    destino: Path,
    sobrescribir: bool = False,
) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not sobrescribir:
        raise FileExistsError(f"Ya existe la salida y no se sobrescribe: {destino}")

    temporal = destino.with_name(f".{destino.name}.{uuid.uuid4().hex}.tmp")
    try:
        tabla.to_parquet(temporal, index=False)
        verificacion = pd.read_parquet(temporal)
        if len(verificacion) != len(tabla):
            raise RuntimeError(
                f"Verificacion fallida para {destino}: {len(verificacion)} != {len(tabla)}."
            )
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino


def _json_default(valor: Any) -> Any:
    if isinstance(valor, Path):
        return str(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if hasattr(valor, "item"):
        return valor.item()
    raise TypeError(f"No se puede serializar {type(valor).__name__}.")


def escribir_json_atomico(
    contenido: dict[str, Any],
    destino: Path,
    sobrescribir: bool = False,
) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists() and not sobrescribir:
        raise FileExistsError(f"Ya existe el manifiesto: {destino}")

    temporal = destino.with_name(f".{destino.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporal.write_text(
            json.dumps(
                contenido,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                default=_json_default,
            )
            + "\n",
            encoding="utf-8",
        )
        json.loads(temporal.read_text(encoding="utf-8"))
        os.replace(temporal, destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino


def ahora_proyecto() -> datetime:
    return datetime.now(tz=ZONA_HORARIA_PROYECTO)


def detectar_commit(repo_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def formatear_duracion(segundos: float) -> str:
    total = max(0, int(round(segundos)))
    horas, resto = divmod(total, 3600)
    minutos, segundos_restantes = divmod(resto, 60)
    return f"{horas} h {minutos} min {segundos_restantes} s"
