# Estado del pipeline: temperatura maxima

**Actualizado:** 29 de julio de 2026
**Estado:** piloto pendiente  
**Fuente:** `ccvq-rp9s`  
**Alcance objetivo:** Boyaca y Cundinamarca, 2024-2025

- [P] **01 Crudo:** 2024-2025 fue reportado por el equipo; la auditoria disponible confirma 2025 y falta verificar 2024.
- [P] **02 Auditoria cruda:** ambos departamentos fueron auditados para 2025; falta evidencia de 2024. Existe al menos un conflicto de valores para una misma clave temporal.
- [P] **Contrato:** `TemperatureRules.py` implementa maximo diario, conserva auxiliares y excluye conflictos; falta validacion con datos reales.
- [ ] **03 Diario por sensor:** ejecutar un piloto pequeno de 2025 y comprobar la exportacion de conflictos.
- [ ] **04 Auditoria diaria:** revisar calendario, cobertura, extremos y coherencia con temperatura ambiente/minima.
- [ ] **05 Curado por estacion:** contrato no implementado; no usar reglas de precipitacion.
- [ ] **Escala 2024-2025:** bloqueada hasta verificar 2024 y aprobar el piloto.
- [ ] **06 Geografia:** pendiente de una capa diaria curada para conocer sus estaciones.
- [ ] **07 Municipio diario:** pendiente.
- [ ] **08 Indicadores por periodo:** pendiente.

Referencias:
[`../temperature_daily_processing.md`](../temperature_daily_processing.md) y
[`../climate_audits/02_datos_crudos/auditoria_temperatura_2024_2025.md`](../climate_audits/02_datos_crudos/auditoria_temperatura_2024_2025.md).

## Siguiente paso exacto

1. Ejecutar 02 para confirmar ambos departamentos en 2024 y contrastar
   enero-febrero de 2025.
2. Configurar 03 con `temperatura_maxima`, fuente `ccvq-rp9s`, ambos
   departamentos, 2025 y meses `[1, 2]`.
3. Confirmar que el plan usa `temperatura_diaria_v2`, ejecutar el piloto y
   verificar que `conflictos.parquet` conserve claves con valores distintos.
4. Auditar esas cuatro particiones con 04 v2.
5. Detenerse y revisar extremos, cobertura y coherencia con ambiente/minima
   antes de disenar 05.
