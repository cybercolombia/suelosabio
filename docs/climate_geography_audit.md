# Auditoria geografica climatica

**Actualizado:** 29 de julio de 2026
**Estado:** corrida espacial v3 verificada; cierre operativo aprobado
**Alcance:** estaciones de precipitacion de Boyaca y Cundinamarca, 2024-2025

`06_Climate_Precipitation_GeographyAudit.ipynb` conecta la capa estacion-dia con los catalogos
IDEAM y DIVIPOLA sin modificar las fuentes compartidas.

## Entradas y escritura

Entradas de solo lectura:

```text
/content/drive/MyDrive/eco2026/
  Estaciones_IDEAM_20260527.csv
  Divipola.csv
  Divipola_Municipios.json
  Boyaca_Cundinamarca_Municipios.gpkg

/content/drive/MyDrive/eco2026_processed/
  clima_diario_curado/variable=precipitacion/.../cierre_precipitacion_2024_2025_v2/
```

Salida personal:

```text
/content/drive/MyDrive/eco2026_processed/
  geografia_curada/canonica=estaciones_precipitacion_2024_2025_v3/
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

`climate_station_geography_v3` conserva codigo de estacion como texto, valida
los 239 poligonos contra DIVIPOLA y ejecuta punto-en-poligono con las
coordenadas oficiales IDEAM.

Una estacion se declara canonica solamente cuando intersecta un unico poligono,
el departamento esta en alcance y el codigo espacial no contradice un codigo
de catalogo conocido. Los conflictos permanecen en
`estaciones_revision.parquet`. Las estaciones fuera de Boyaca y Cundinamarca,
incluida Bogota D.C. aunque la descarga la haya agrupado bajo Cundinamarca,
quedan en `estaciones_excluidas.parquet` y no cuentan como revisiones
pendientes.

## Cierre espacial v2

El GeoPackage contiene una capa `Boyaca_Cundinamarca_Municipios` con CRS
`EPSG:4326`, 239 `MultiPolygon` validos y 239 codigos compuestos unicos:
123 municipios de Boyaca y 116 de Cundinamarca. Los codigos concuerdan
exactamente con DIVIPOLA.

La corrida persistida el 29 de julio de 2026 sobre las 126 estaciones produjo:

- 112 puntos donde poligono y catalogo coinciden.
- 4 nombres no resueltos por catalogo que el poligono resuelve.
- 7 conflictos entre municipio de catalogo y municipio espacial.
- 3 puntos sin poligono contenedor, incluido uno fuera del alcance.
- 116 asignaciones canonicas y 10 estaciones no canonicas.
- 84 municipios representados por al menos una estacion canonica.
- Ninguna estacion de Bogota dentro del catalogo canonico.

Los diez casos no canonicos se componen de siete conflictos catalogo-poligono,
dos puntos cercanos a limites sin poligono contenedor y una estacion de Bogota
D.C. fuera del alcance. Esta ultima motivó el contrato v3: deja de contarse como
revision y se conserva como exclusion explicita.

## Cierre historico sin poligonos

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

La corrida v3 persistida confirmo 116 asignaciones canonicas, 9 revisiones y
1 exclusion de alcance. El paso 07 puede consumir exclusivamente
las filas de `estaciones_municipio.parquet`, que contienen
`asignacion_canonica=True`. Las nueve estaciones en revision y la exclusion de
Bogota no se eliminan, pero tampoco se agregan silenciosamente a un municipio.
