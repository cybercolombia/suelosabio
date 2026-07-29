# Auditorias de datos climaticos crudos

Estos reportes se producen a partir de `clima_crudo` con
`02_ClimateDataAudit.ipynb`. Evaluan estructura, particiones, tipos, unidades,
nulos, conversiones, duplicados, conflictos, cadencias y geografia antes de
transformar observaciones subdiarias.

El inventario de archivos y filas puede ser completo, pero las metricas de
calidad suelen ser muestrales. Cada reporte declara su alcance.

## Modos de ejecucion

Las cuatro banderas permanecen en `False` en Git y se activa un solo modo por
corrida.

### Auditoria por muestra

```python
EJECUTAR_INVENTARIO_GENERAL = False
EJECUTAR_AUDITORIA = True
EJECUTAR_CONTEO_ESTACIONES_COMPLETO = False
EJECUTAR_INVENTARIO_OPERATIVO = False
```

### Auditoria con conteo completo de estaciones

Usa la configuracion anterior y cambia
`EJECUTAR_CONTEO_ESTACIONES_COMPLETO=True`. Esto vuelve exactos el conteo y
rango temporal por estacion-sensor, pero no convierte las demas metricas
muestrales en analisis completos.

### Inventarios independientes

- Inventario general aproximado: solo `EJECUTAR_INVENTARIO_GENERAL=True`.
- Inventario operativo de particiones: solo
  `EJECUTAR_INVENTARIO_OPERATIVO=True`.

Los reportes deben identificar variable, fuente, departamentos, periodo y modo.
Los Parquet exportados conservan todas las filas detectadas; el Markdown limita
las vistas extensas.

## Reportes

- [Precipitacion, Boyaca y Cundinamarca, 2024](auditoria_precipitacion_2024.md)
- [Precipitacion, Boyaca, 2025](auditoria_precipitacion_boyaca_2025.md)
- [Precipitacion, Boyaca, 2021 y 2023](auditoria_precipitacion_boyaca_2021_2023.md)
- [Precipitacion, Cundinamarca, 2025](auditoria_precipitacion_cundinamarca_2025.md)
- [Precipitacion, Cundinamarca, 2021 y 2023](auditoria_precipitacion_cundinamarca_2021_2023.md)
- [Humedad, Cundinamarca, 2025](auditoria_humedad_cundinamarca_2025.md)
- [Temperatura, Boyaca y Cundinamarca, 2024-2025](auditoria_temperatura_2024_2025.md)
