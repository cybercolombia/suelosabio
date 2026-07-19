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
EJECUTAR_INVENTARIO_OPERATIVO = False
```

### Auditoria por muestra

Audita una variable, departamentos y periodos concretos. El inventario de filas
es exacto por metadatos; calidad, duplicados y frecuencia se estudian sobre una
muestra estratificada.

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = True
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = False
EJECUTAR_INVENTARIO_OPERATIVO = False
```

### Auditoria con conteo completo de estaciones

Incluye todo lo anterior y recorre todos los Parquet seleccionados leyendo solo
estacion, sensor y fecha. No convierte el resto de la auditoria muestral en un
analisis completo.

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = True
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = True
EJECUTAR_INVENTARIO_OPERATIVO = False
```

### Inventario operativo final

Revisa las particiones esperadas por variable, departamento, ano y mes sin abrir
los Parquet. Esta es una seccion independiente ubicada al final del notebook.

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = False
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = False
EJECUTAR_INVENTARIO_OPERATIVO = True
```

Las cuatro banderas permanecen en `False` en Git. Para una auditoria historica
de 2021 o 2023 basta con configurar un departamento y un ano, activar
`EJECUTAR_AUDITORIA` y conservar el conteo completo desactivado.

## Exportacion

Los Parquet guardan todas las filas duplicadas, claves repetidas, conflictos y
fechas fuera de particion detectadas en la muestra. El Markdown limita cada vista
a 50 filas e incluye resumen de cadencias, actividad mensual y alertas
geograficas medidas en metros.

## Nombres de reportes

Los reportes deben identificar variable, fuente, departamentos, periodo y modo.
Ejemplo:

```text
AuditoriaClimatica_humedad_uext_mhny_cundinamarca_2025_conteo_completo.md
```

## Sintesis disponibles

- [Precipitacion, Cundinamarca, 2025](auditoria_precipitacion_cundinamarca_2025.md)
- [Precipitacion, Cundinamarca, 2021 y 2023](auditoria_precipitacion_cundinamarca_2021_2023.md)
- [Precipitacion, Boyaca, 2025](auditoria_precipitacion_boyaca_2025.md)
- [Precipitacion, Boyaca, 2021 y 2023](auditoria_precipitacion_boyaca_2021_2023.md)
- [Humedad, Cundinamarca, 2025](auditoria_humedad_cundinamarca_2025.md)
