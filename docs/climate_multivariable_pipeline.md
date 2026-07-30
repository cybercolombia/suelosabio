# Pipeline climático multivariable

La rama `feature/SCRUM-16` separa los notebooks por variable para impedir que
una configuración de precipitación se reutilice accidentalmente con otra
unidad o estadístico.

## Alcance 2024–2025

| Variable | Dataset IDEAM | Estadístico diario | Unidad |
|---|---|---|---|
| Precipitación | `s54a-sgyg` | suma | mm |
| Temperatura ambiente | `sbwg-7ju4` | media | °C |
| Temperatura mínima | `afdg-3zpb` | mínimo | °C |
| Temperatura máxima | `ccvq-rp9s` | máximo | °C |
| Velocidad del viento | `sgfv-3yp8` | media | m/s |
| Presión atmosférica | `62tk-nxj5` | media | hPa |

El alcance espacial es Boyacá y Cundinamarca. Cada variable dispone de
notebooks independientes para:

1. descarga incremental;
2. auditoría del dato crudo;
3. transformación estación-sensor-día;
4. auditoría diaria;
5. consolidación estación-día;
6. auditoría y asignación geográfica;
7. agregación municipio-día.

Los nombres siguen el patrón
`NN_Climate_{Variable}_{Operacion}.ipynb`. Precipitación conserva además el
notebook `07_2_Climate_Precipitation_MunicipalAudit.ipynb`.

## Inventario de datos crudos

El inventario incremental del 29 de julio de 2026 revisó los metadatos Parquet
de las 48 particiones esperadas por variable: dos departamentos, dos años y
doce meses. Las cinco variables nuevas presentaron 48 de 48 particiones
cerradas, secuencias continuas de archivos `part-xxxxx.parquet` y un último
lote menor de 1.000 filas. No fue necesario descargar ni sobrescribir datos.

## Contratos de calidad

- Los sensores permanecen separados hasta la consolidación.
- Una cobertura no evaluable, menor a 90 % o mayor a 102 % no produce un valor
  estación-día aceptado.
- Los valores sospechosos permanecen trazables y no se imputan.
- Si dos sensores válidos superan la tolerancia de su variable, el valor
  estación-día queda nulo con calidad `SENSORES_DISCREPANTES`.
- El valor municipio-día es la mediana no ponderada de estaciones aceptadas.
- Cada variable usa su propia geografía canónica para no asumir que todas las
  redes de estaciones son idénticas.

## Ejecución segura

Todos los notebooks mantienen su bandera principal en `False`. Desde terminal
se pueden reanudar explícitamente con `ClimateNotebookRunner.py`, indicando
únicamente la bandera que se desea habilitar. Los manifiestos `COMPLETA`
permiten omitir resultados terminados y las escrituras se hacen de forma
atómica.

Las salidas se almacenan bajo la raíz configurada por `DatasetConfig.py`.
En Colab se monta Google Drive; en local se usa la ruta compartida configurada
para el proyecto.

## Cierre de ejecución

El 29 de julio de 2026 se completaron las etapas 01–07 para temperatura
ambiente, temperatura mínima, temperatura máxima, velocidad del viento y
presión atmosférica. Las cinco variables tienen 48 particiones diarias
`COMPLETA`, auditoría diaria, consolidación estación-día, geografía construida
desde los catálogos oficiales y agregación para los 239 municipios.

Las fuentes geográficas locales se leen desde:

```text
/Users/eshernan/Library/CloudStorage/
GoogleDrive-eshernan@gmail.com/My Drive/eco2026
```

En Colab, la ruta equivalente es `/content/drive/MyDrive/eco2026`.
