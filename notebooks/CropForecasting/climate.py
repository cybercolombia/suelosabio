"""Clima diario NASA POWER y sus indicadores por municipio-semestre."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
from pathlib import Path
import time
from typing import Iterable
from urllib.parse import urlencode

import geopandas as gpd
import numpy as np
import pandas as pd
import requests


NASA_ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_PARAMETERS = (
    "PRECTOTCORR",
    "T2M",
    "T2M_MIN",
    "T2M_MAX",
    "RH2M",
    "WS2M",
    "PS",
)
NASA_FILL_VALUE = -999.0
GRID_STEP_DEGREES = 0.5
CLIMATE_START = "20190101"
CLIMATE_END = "20260730"


def municipality_grid(path: str | Path) -> pd.DataFrame:
    """Asigna cada municipio a una celda POWER reproducible de 0,5 grados."""
    geography = gpd.read_file(path)
    required = {"DPTO_CCDGO", "MPIO_CCDGO", "MPIO_CNMBR", "geometry"}
    missing = required - set(geography.columns)
    if missing:
        raise ValueError(f"Faltan columnas geográficas: {sorted(missing)}")
    if geography.crs is None:
        raise ValueError("La geografía municipal no declara CRS.")
    geography = geography.to_crs(4326).copy()
    points = geography.geometry.representative_point()
    result = pd.DataFrame(
        {
            "codigo_departamento": geography["DPTO_CCDGO"].astype("string").str.zfill(2),
            "codigo_municipio": (
                geography["DPTO_CCDGO"].astype("string").str.zfill(2)
                + geography["MPIO_CCDGO"].astype("string").str.zfill(3)
            ),
            "municipio_geografia": geography["MPIO_CNMBR"].astype("string"),
            "longitud": points.x.astype(float),
            "latitud": points.y.astype(float),
        }
    )
    result["grid_longitud"] = result["longitud"].map(_grid_center)
    result["grid_latitud"] = result["latitud"].map(_grid_center)
    if result["codigo_municipio"].duplicated().any():
        raise ValueError("La geografía contiene códigos municipales repetidos.")
    return result.sort_values("codigo_municipio").reset_index(drop=True)


def _grid_center(value: float, step: float = GRID_STEP_DEGREES) -> float:
    return round(math.floor(float(value) / step + 0.5) * step, 3)


def _cache_name(latitude: float, longitude: float) -> str:
    lat = f"{latitude:+07.3f}".replace("+", "p").replace("-", "m").replace(".", "_")
    lon = f"{longitude:+08.3f}".replace("+", "p").replace("-", "m").replace(".", "_")
    return f"grid_lat={lat}_lon={lon}.json"


def _request_power(
    latitude: float,
    longitude: float,
    *,
    start: str,
    end: str,
    timeout: int = 120,
    request_get=requests.get,
) -> dict:
    query = urlencode(
        {
            "parameters": ",".join(NASA_PARAMETERS),
            "community": "AG",
            "longitude": longitude,
            "latitude": latitude,
            "start": start,
            "end": end,
            "format": "JSON",
            "time-standard": "LST",
        }
    )
    with request_get(
        f"{NASA_ENDPOINT}?{query}",
        timeout=(10, timeout),
        verify=True,
    ) as response:
        response.raise_for_status()
        payload = response.json()
    observed = set(payload.get("properties", {}).get("parameter", {}))
    if observed != set(NASA_PARAMETERS):
        raise ValueError(
            f"POWER devolvió parámetros inesperados para {latitude}, {longitude}: "
            f"{sorted(observed)}"
        )
    return payload


def download_power_cells(
    municipality_cells: pd.DataFrame,
    output_root: str | Path,
    *,
    start: str = CLIMATE_START,
    end: str = CLIMATE_END,
    max_workers: int = 4,
    retries: int = 3,
) -> list[Path]:
    """Descarga una sola vez cada celda y reutiliza caches completos."""
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    cells = municipality_cells[["grid_latitud", "grid_longitud"]].drop_duplicates()

    def fetch(row: tuple[float, float]) -> Path:
        latitude, longitude = row
        target = root / _cache_name(latitude, longitude)
        if target.exists():
            payload = json.loads(target.read_text(encoding="utf-8"))
            header = payload.get("header", {})
            if header.get("start") == start and header.get("end") == end:
                return target
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                payload = _request_power(
                    latitude, longitude, start=start, end=end
                )
                temporary = target.with_suffix(".json.tmp")
                temporary.write_text(
                    json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8",
                )
                temporary.replace(target)
                return target
            except Exception as exc:  # pragma: no cover - depende de red externa
                last_error = exc
                if attempt < retries:
                    time.sleep(2**attempt)
        raise RuntimeError(
            f"Falló NASA POWER para {latitude}, {longitude}"
        ) from last_error

    paths: list[Path] = []
    rows = [tuple(row) for row in cells.itertuples(index=False, name=None)]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch, row): row for row in rows}
        for future in as_completed(futures):
            paths.append(future.result())
    return sorted(paths)


def read_power_daily(
    municipality_cells: pd.DataFrame,
    cache_paths: Iterable[str | Path],
) -> pd.DataFrame:
    """Expande las celdas climáticas hacia los municipios que representan."""
    frames: list[pd.DataFrame] = []
    for cache_path in cache_paths:
        payload = json.loads(Path(cache_path).read_text(encoding="utf-8"))
        parameters = payload["properties"]["parameter"]
        coordinates = payload["geometry"]["coordinates"]
        longitude, latitude = float(coordinates[0]), float(coordinates[1])
        dates = sorted(next(iter(parameters.values())))
        frame = pd.DataFrame({"fecha": pd.to_datetime(dates, format="%Y%m%d")})
        for parameter in NASA_PARAMETERS:
            values = pd.Series(parameters[parameter], dtype=float)
            frame[parameter] = [
                np.nan
                if float(values[date]) <= NASA_FILL_VALUE
                else float(values[date])
                for date in dates
            ]
        frame["grid_latitud"] = latitude
        frame["grid_longitud"] = longitude
        frames.append(frame)
    cells_daily = pd.concat(frames, ignore_index=True)
    cells = municipality_cells.copy()
    # POWER devuelve el mismo punto solicitado, con precisión JSON suficiente.
    cells["grid_latitud"] = cells["grid_latitud"].astype(float)
    cells["grid_longitud"] = cells["grid_longitud"].astype(float)
    daily = cells.merge(
        cells_daily,
        on=["grid_latitud", "grid_longitud"],
        how="left",
        validate="many_to_many",
    )
    if daily["fecha"].isna().any():
        missing = daily.loc[daily["fecha"].isna(), "codigo_municipio"].unique()
        raise RuntimeError(f"Municipios sin clima POWER: {missing[:10].tolist()}")
    if daily.duplicated(["codigo_municipio", "fecha"]).any():
        raise RuntimeError("POWER produjo llaves municipio-fecha repetidas.")
    return daily.sort_values(["codigo_municipio", "fecha"]).reset_index(drop=True)


def _longest_dry_spell(values: pd.Series) -> int:
    dry = values.fillna(np.inf).lt(1.0)
    groups = (~dry).cumsum()
    counts = dry.groupby(groups).sum()
    return int(counts.max()) if len(counts) else 0


def aggregate_semester_indicators(daily: pd.DataFrame) -> pd.DataFrame:
    """Resume clima por semestre conservando extremos, persistencia y perfil."""
    required = {"codigo_municipio", "fecha", *NASA_PARAMETERS}
    missing = required - set(daily.columns)
    if missing:
        raise ValueError(f"Faltan columnas POWER diarias: {sorted(missing)}")
    data = daily.copy()
    data["fecha"] = pd.to_datetime(data["fecha"], errors="coerce")
    if data["fecha"].isna().any():
        raise ValueError("Hay fechas POWER inválidas.")
    data["anio"] = data["fecha"].dt.year.astype(int)
    data["tipo_periodo"] = np.where(data["fecha"].dt.month <= 6, "A", "B")
    month_in_semester = (data["fecha"].dt.month - 1) % 6
    data["bloque_semestre"] = (month_in_semester // 2 + 1).astype(int)
    data["rango_termico_diario"] = data["T2M_MAX"] - data["T2M_MIN"]
    data["dia_humedo"] = data["PRECTOTCORR"].ge(1.0)
    data["dia_calido"] = data["T2M_MAX"].gt(25.0)
    data["dia_frio"] = data["T2M_MIN"].lt(5.0)
    keys = ["codigo_municipio", "anio", "tipo_periodo"]
    indicators = (
        data.groupby(keys, as_index=False)
        .agg(
            dias_esperados=("fecha", "size"),
            dias_clima_observados=("T2M", "count"),
            precipitacion_total_mm=("PRECTOTCORR", "sum"),
            precipitacion_media_mm_dia=("PRECTOTCORR", "mean"),
            precipitacion_max_1d_mm=("PRECTOTCORR", "max"),
            dias_humedos=("dia_humedo", "sum"),
            racha_seca_max_dias=("PRECTOTCORR", _longest_dry_spell),
            temperatura_media_c=("T2M", "mean"),
            temperatura_std_c=("T2M", "std"),
            temperatura_min_media_c=("T2M_MIN", "mean"),
            temperatura_min_abs_c=("T2M_MIN", "min"),
            temperatura_max_media_c=("T2M_MAX", "mean"),
            temperatura_max_abs_c=("T2M_MAX", "max"),
            rango_termico_medio_c=("rango_termico_diario", "mean"),
            dias_calidos=("dia_calido", "sum"),
            dias_frios=("dia_frio", "sum"),
            humedad_media_pct=("RH2M", "mean"),
            humedad_std_pct=("RH2M", "std"),
            viento_medio_ms=("WS2M", "mean"),
            viento_max_ms=("WS2M", "max"),
            presion_media_kpa=("PS", "mean"),
            presion_std_kpa=("PS", "std"),
        )
    )
    observed = (
        data.groupby(keys)[list(NASA_PARAMETERS)]
        .count()
        .min(axis=1)
        .rename("dias_todas_variables")
        .reset_index()
    )
    indicators = indicators.merge(observed, on=keys, validate="one_to_one")
    indicators["cobertura_climatica_pct"] = (
        100 * indicators["dias_todas_variables"] / indicators["dias_esperados"]
    )

    block = (
        data.groupby([*keys, "bloque_semestre"], as_index=False)
        .agg(
            precipitacion_bloque_mm=("PRECTOTCORR", "sum"),
            temperatura_bloque_c=("T2M", "mean"),
            humedad_bloque_pct=("RH2M", "mean"),
        )
    )
    for metric in (
        "precipitacion_bloque_mm",
        "temperatura_bloque_c",
        "humedad_bloque_pct",
    ):
        wide = block.pivot(
            index=keys, columns="bloque_semestre", values=metric
        ).rename(columns=lambda number: f"{metric}_{int(number)}")
        indicators = indicators.merge(
            wide.reset_index(), on=keys, how="left", validate="one_to_one"
        )
    if indicators.duplicated(keys).any():
        raise RuntimeError("Los indicadores climáticos tienen llaves repetidas.")
    return indicators.sort_values(keys).reset_index(drop=True)


def build_asof_climate_scenario(
    daily: pd.DataFrame,
    forecast_year: int,
    *,
    cutoff_month: int = 7,
    cutoff_day: int = 30,
) -> pd.DataFrame:
    """Crea el clima conocido al 30 de julio y completa el futuro con climatología.

    Para el semestre A se usan observaciones del propio año. Para el semestre B
    se conservan los días observados hasta la fecha de corte y se completa el
    resto con el promedio diario de todos los años anteriores disponibles.
    """
    data = daily.copy()
    data["fecha"] = pd.to_datetime(data["fecha"], errors="coerce")
    if data["fecha"].isna().any():
        raise ValueError("El escenario recibió fechas inválidas.")
    year = int(forecast_year)
    if year <= int(data["fecha"].dt.year.min()):
        raise ValueError("El escenario requiere al menos un año climático anterior.")
    history = data[data["fecha"].dt.year < year].copy()
    current = data[data["fecha"].dt.year.eq(year)].copy()
    if history.empty:
        raise ValueError(f"No hay historia climática anterior a {year}.")

    history["mes"] = history["fecha"].dt.month
    history["dia"] = history["fecha"].dt.day
    climatology = (
        history.groupby(["codigo_municipio", "mes", "dia"], as_index=False)[
            list(NASA_PARAMETERS)
        ]
        .mean()
    )
    municipalities = data[
        [
            "codigo_departamento",
            "codigo_municipio",
            "municipio_geografia",
            "longitud",
            "latitud",
            "grid_longitud",
            "grid_latitud",
        ]
    ].drop_duplicates("codigo_municipio")
    calendar = pd.DataFrame(
        {"fecha": pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")}
    )
    scenario = municipalities.merge(calendar, how="cross")
    scenario["mes"] = scenario["fecha"].dt.month
    scenario["dia"] = scenario["fecha"].dt.day
    scenario = scenario.merge(
        climatology,
        on=["codigo_municipio", "mes", "dia"],
        how="left",
        validate="many_to_one",
        suffixes=("", "_climatologia"),
    )
    actual_columns = ["codigo_municipio", "fecha", *NASA_PARAMETERS]
    actual = current[actual_columns].rename(
        columns={parameter: f"{parameter}_real" for parameter in NASA_PARAMETERS}
    )
    scenario = scenario.merge(
        actual,
        on=["codigo_municipio", "fecha"],
        how="left",
        validate="one_to_one",
    )
    cutoff = pd.Timestamp(year=year, month=cutoff_month, day=cutoff_day)
    use_actual = scenario["fecha"].le(cutoff)
    actual_available = pd.Series(True, index=scenario.index)
    for parameter in NASA_PARAMETERS:
        real = scenario[f"{parameter}_real"]
        actual_available &= real.notna()
        scenario[parameter] = real.where(use_actual & real.notna(), scenario[parameter])
    scenario["origen_clima_dia"] = np.where(
        use_actual & actual_available,
        "OBSERVADO",
        "CLIMATOLOGIA_HISTORICA",
    )
    if scenario[list(NASA_PARAMETERS)].isna().any().any():
        missing = scenario.loc[
            scenario[list(NASA_PARAMETERS)].isna().any(axis=1),
            ["codigo_municipio", "fecha"],
        ]
        raise RuntimeError(
            "No fue posible completar el escenario climático: "
            f"{missing.head().to_dict(orient='records')}"
        )
    keep = [
        *municipalities.columns,
        "fecha",
        *NASA_PARAMETERS,
        "origen_clima_dia",
    ]
    return scenario[keep].sort_values(
        ["codigo_municipio", "fecha"]
    ).reset_index(drop=True)


def aggregate_asof_semester_indicators(scenario: pd.DataFrame) -> pd.DataFrame:
    """Agrega un escenario y conserva cuántos días son reales o climatológicos."""
    indicators = aggregate_semester_indicators(scenario)
    origin = scenario.copy()
    origin["anio"] = origin["fecha"].dt.year.astype(int)
    origin["tipo_periodo"] = np.where(origin["fecha"].dt.month <= 6, "A", "B")
    origin["_real"] = origin["origen_clima_dia"].eq("OBSERVADO")
    counts = (
        origin.groupby(
            ["codigo_municipio", "anio", "tipo_periodo"], as_index=False
        )
        .agg(
            dias_clima_real=("_real", "sum"),
            dias_clima_climatologia=("_real", lambda value: int((~value).sum())),
        )
    )
    result = indicators.merge(
        counts,
        on=["codigo_municipio", "anio", "tipo_periodo"],
        validate="one_to_one",
    )
    result["tipo_escenario_climatico"] = np.where(
        result["dias_clima_climatologia"].eq(0),
        "OBSERVADO_COMPLETO",
        "OBSERVADO_MAS_CLIMATOLOGIA",
    )
    return result
