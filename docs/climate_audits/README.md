# Auditorias climaticas

Esta carpeta conserva reportes legibles derivados de `02_ClimateDataAudit.ipynb`.
Los Parquet crudos no se modifican durante una auditoria.

## Modos de ejecucion

### Inventario general aproximado

Recorre `clima_crudo`, cuenta archivos `part-*.parquet` y estima como maximo
1.000 registros por archivo. No abre los Parquet.

```python
EJECUTAR_INVENTARIO_GENERAL = True
EJECUTAR_AUDITORIA = False
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = False
```

### Auditoria por muestra

Audita una variable, departamentos y periodos concretos. El inventario de filas
es exacto por metadatos; calidad, duplicados y frecuencia se estudian sobre una
muestra estratificada.

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = True
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = False
```

### Auditoria con conteo completo de estaciones

Incluye todo lo anterior y recorre todos los Parquet seleccionados leyendo solo
estacion, sensor y fecha. No convierte el resto de la auditoria muestral en un
analisis completo.

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = True
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = True
```

## Nombres de reportes

Los reportes deben identificar variable, fuente, departamentos, periodo y modo.
Ejemplo:

```text
AuditoriaClimatica_humedad_uext_mhny_cundinamarca_2025_conteo_completo.md
```
