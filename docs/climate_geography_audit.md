# Auditoria geografica climatica

**Actualizado:** 28 de julio de 2026
**Estado:** contrato espacial v2 implementado; corrida persistida pendiente
**Alcance:** estaciones de precipitacion de Boyaca y Cundinamarca, 2024-2025

`06_ClimateGeographyAudit.ipynb` conecta la capa estacion-dia con los catalogos
IDEAM y DIVIPOLA sin modificar las fuentes compartidas.

## Entradas y escritura

Entradas de solo lectura:

```text
/content/drive/MyDrive/eco2026/
  Estaciones_IDEAM_20260527.csv
  Divipola.csv
  Divipola_Municipios.json

/content/drive/MyDrive/eco2026_processed/
  geografia_fuente/DivipolaGeo.gpkg
  clima_diario_curado/variable=precipitacion/.../cierre_precipitacion_2024_2025_v2/
```

Salida personal:

```text
/content/drive/MyDrive/eco2026_processed/
  geografia_curada/canonica=estaciones_precipitacion_2024_2025_v2/
```

El notebook comprueba que la ruta de salida no pertenezca a `eco2026`.

## Ejecucion segura

1. Ejecutar todo con `EJECUTAR_AUDITORIA_GEOGRAFICA=False`.
2. Confirmar clima `COMPLETA`, 48 particiones y los tres catalogos disponibles.
3. Cambiar solo `EJECUTAR_AUDITORIA_GEOGRAFICA=True`.
4. Mantener `GUARDAR_RESULTADOS=True` y `SOBRESCRIBIR_RESULTADOS=False`.
5. Ejecutar desde la configuracion hasta el final.
6. Volver a dejar la bandera en `False` antes de guardar el notebook.

## Contrato actual

`climate_station_geography_v2` conserva codigo de estacion como texto, valida
los 239 poligonos contra DIVIPOLA y ejecuta punto-en-poligono con las
coordenadas oficiales IDEAM.

Una estacion se declara canonica solamente cuando intersecta un unico poligono,
el departamento esta en alcance y el codigo espacial no contradice un codigo
de catalogo conocido. Los conflictos permanecen en
`estaciones_revision.parquet`.

## Prevalidacion local v2

El GeoPackage contiene una capa `Boyaca_Cundinamarca_Municipios` con CRS
`EPSG:4326`, 239 `MultiPolygon` validos y 239 codigos compuestos unicos:
123 municipios de Boyaca y 116 de Cundinamarca. Los codigos concuerdan
exactamente con DIVIPOLA.

La prueba completa sobre las 126 estaciones produjo:

- 112 puntos donde poligono y catalogo coinciden.
- 4 nombres no resueltos por catalogo que el poligono resuelve.
- 7 conflictos entre municipio de catalogo y municipio espacial.
- 3 puntos sin poligono contenedor, incluido uno fuera del alcance.
- 116 asignaciones canonicas y 10 estaciones para revision.

Estas cifras son una expectativa de control. El estado oficial se actualizara
despues de persistir la corrida v2 en Drive.

## Cierre ejecutado

La ejecucion `estaciones_precipitacion_2024_2025_v1` termino el 24 de julio de
2026 con estado `COMPLETA_SIN_POLIGONOS`:

- 48 particiones y 53.128 filas estacion-dia como entrada.
- 126 estaciones climaticas unicas, todas encontradas en el catalogo IDEAM.
- 111 candidatos sin alertas de catalogo y 15 estaciones para revision.
- 122 candidatos DIVIPOLA resueltos por nombre normalizado.
- Cero estaciones duplicadas, cero coordenadas IDEAM faltantes y cero
  asignaciones declaradas canonicas.
- Mapa HTML, cinco tablas Parquet, manifiesto y reporte persistidos.

La evidencia resumida esta en
[`climate_audits/06_geografia/auditoria_geografica_precipitacion_2024_2025.md`](climate_audits/06_geografia/auditoria_geografica_precipitacion_2024_2025.md).

## Compuerta antes de 07

Despues de ejecutar y persistir v2, el paso 07 puede consumir exclusivamente
las filas de `estaciones_municipio.parquet`, que contienen
`asignacion_canonica=True`. Las diez estaciones en revision no se eliminan,
pero tampoco se agregan silenciosamente a un municipio.
