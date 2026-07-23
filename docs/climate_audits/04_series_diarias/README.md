# Auditorias de series climaticas diarias

Estos reportes se producen a partir de `clima_diario_sensor` con
`04_ClimateDailyAudit.ipynb`. Evaluan el calendario estacion-sensor-dia,
cobertura, brechas, extremos y sensores paralelos despues de aplicar las reglas
del paso 03.

Una auditoria diaria no reemplaza la auditoria de datos crudos: responde
preguntas nuevas creadas por la transformacion.

Para precipitacion, la version `auditoria_precipitacion_diaria_v2` incorpora un
catalogo estacion-sensor, actividad mensual esperada dentro del intervalo
observado y deteccion de meses completamente ausentes.

## Reportes

- [Piloto diario de precipitacion, enero y febrero de 2025](auditoria_piloto_diario_precipitacion_2025.md)
