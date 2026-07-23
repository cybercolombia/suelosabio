# Estado del pipeline: temperatura minima

**Actualizado:** 22 de julio de 2026  
**Estado:** piloto pendiente  
**Fuente:** `afdg-3zpb`  
**Alcance objetivo:** Boyaca y Cundinamarca, 2024-2025

- [P] **01 Crudo:** 2024-2025 fue reportado por el equipo; la auditoria disponible confirma 2025 y falta verificar 2024.
- [P] **02 Auditoria cruda:** ambos departamentos fueron auditados para 2025; falta evidencia de 2024 y contraste temporal.
- [P] **Contrato:** `TemperatureRules.py` implementa minimo diario y estadisticos auxiliares; falta validacion con datos reales.
- [ ] **03 Diario por sensor:** ejecutar un piloto pequeno de 2025 despues de confirmar el crudo.
- [ ] **04 Auditoria diaria:** revisar calendario, cobertura, extremos y coherencia con temperatura ambiente/maxima.
- [ ] **05 Curado por estacion:** contrato no implementado; no usar reglas de precipitacion.
- [ ] **Escala 2024-2025:** bloqueada hasta verificar 2024 y aprobar el piloto.
- [ ] **06 Municipio y periodo:** pendiente.

Referencias:
[`../temperature_daily_processing.md`](../temperature_daily_processing.md) y
[`../climate_audits/02_datos_crudos/auditoria_temperatura_2024_2025.md`](../climate_audits/02_datos_crudos/auditoria_temperatura_2024_2025.md).
