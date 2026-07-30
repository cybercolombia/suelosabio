# Auditoria geografica de precipitacion 2024-2025

**Fecha de ejecucion espacial:** 29 de julio de 2026
**Fuente climatica:** `s54a-sgyg`
**Contrato ejecutado:** `climate_station_geography_v3`
**Estado:** `COMPLETA_CON_REVISION_PENDIENTE`
**Commit de ejecucion:** `a0ce33708cb7ea9fb51c1b866202af6588e17f2c`

## Entrada y productos

La corrida leyo las 48 particiones y 53.128 filas estacion-dia del cierre
`cierre_precipitacion_2024_2025_v2`. Valido la capa
`Boyaca_Cundinamarca_Municipios` de
`Boyaca_Cundinamarca_Municipios.gpkg` y escribio fuera de la
carpeta compartida.

Productos persistidos:

- Catalogo de 126 estaciones climaticas.
- 116 asignaciones estacion-municipio canonicas.
- 9 estaciones en revision y 1 exclusion de alcance.
- 239 municipios DIVIPOLA y 239 geometrías municipales validas.
- Resumen, mapa HTML, reporte y manifiesto.

## Reconciliacion

| Control | Resultado |
|---|---:|
| Estaciones climaticas unicas | 126 |
| Estaciones encontradas en IDEAM | 126 |
| Asignaciones canonicas | 116 |
| Municipios con estacion canonica | 84 |
| Catalogo y poligono coinciden | 112 |
| Catalogo resuelto solo por poligono | 4 |
| Conflictos catalogo-poligono | 7 |
| Puntos sin poligono contenedor | 3 |
| Estaciones en revision | 9 |
| Estaciones excluidas por alcance | 1 |
| Poligonos municipales validos | 239 |

Las 116 asignaciones canonicas se distribuyen en 59 estaciones de Boyaca y 57
de Cundinamarca. No hay codigos de Bogota dentro del catalogo canonico.

## Casos no canonicos

Los diez casos se separan conceptualmente en:

- Siete conflictos entre el municipio del catalogo IDEAM y el poligono.
- Dos estaciones de Boyaca muy cercanas a un limite, pero sin poligono
  contenedor: `0024035360` y `0024035502`.
- Una estacion fuera del alcance: `2120500204`, IDEAM Puente Aranda, pertenece
  a Bogota D.C. aunque la descarga la agrupo bajo Cundinamarca.

Bogota no es un conflicto pendiente ni una candidata de Cundinamarca. El
contrato ejecutado `climate_station_geography_v3` la conserva en
`estaciones_excluidas.parquet`; las otras nueve permanecen en
`estaciones_revision.parquet`.

## Decision

La corrida v2 se conserva como evidencia historica. La corrida v3 confirmo:

- 116 asignaciones canonicas.
- 9 estaciones en revision geografica.
- 1 estacion excluida por alcance.

El paso 07 puede diseñarse usando exclusivamente `estaciones_municipio.parquet`.
No debe incorporar estaciones en revision ni exclusiones de alcance hasta que
exista una resolucion versionada.
