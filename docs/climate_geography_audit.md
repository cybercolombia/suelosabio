# Auditoria geografica climatica

**Actualizado:** 24 de julio de 2026
**Estado:** cierre tabular y mapa ejecutados; poligonos pendientes
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
  clima_diario_curado/variable=precipitacion/.../cierre_precipitacion_2024_2025_v2/
```

Salida personal:

```text
/content/drive/MyDrive/eco2026_processed/
  geografia_curada/ejecucion=estaciones_precipitacion_2024_2025_v1/
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

`climate_station_geography_v1` conserva codigo de estacion como texto, compara
departamento, municipio y coordenadas, resuelve un candidato DIVIPOLA y genera
un mapa de puntos. El estado esperado es `COMPLETA_SIN_POLIGONOS`.

Los archivos `estaciones_municipio_candidato.parquet` y
`estaciones_revision.parquet` son evidencia preliminar. La columna
`asignacion_canonica` permanece en `False` para todas las filas.

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

La capa `Div_Pol.shp` encontrada carece de componentes esenciales del formato.
Antes de agregar clima por municipio se necesita:

1. Conseguir una capa municipal completa con geometria, atributos y CRS.
2. Filtrar Boyaca y Cundinamarca.
3. Ejecutar punto-en-poligono para cada estacion.
4. Resolver estaciones fuera del alcance, municipios multiples y coordenadas
   discrepantes.
5. Publicar `estaciones_municipio.parquet` como catalogo canonico versionado.
