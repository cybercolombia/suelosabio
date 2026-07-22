# Estado del pipeline: temperatura ambiente

**Actualizado:** 22 de julio de 2026  
**Estado:** piloto pendiente  
**Fuente:** `sbwg-7ju4`  
**Alcance objetivo:** Boyaca y Cundinamarca, 2024-2025

- [P] **01 Crudo:** 2024-2025 fue reportado y observado en las auditorias; falta reconciliacion integral de descargas.
- [X] **02 Auditoria cruda:** ambos departamentos y ambos anos tienen evidencia; deben conservarse febrero de 2025 y meses contrastantes como pruebas de cobertura.
- [P] **Contrato:** `TemperatureRules.py` implementa media diaria, estadisticos auxiliares, deduplicacion, conflictos y rango operativo; falta validarlo con una corrida real.
- [ ] **03 Diario por sensor:** ejecutar primero enero-febrero de 2025 en ambos departamentos y verificar manifiestos `COMPLETA`.
- [ ] **03_01 Auditoria diaria:** validar calendario, cobertura, extremos, amplitud y sensores paralelos del piloto.
- [ ] **04 Curado por estacion:** disenar reglas termicas a partir del piloto; el consolidador de precipitacion esta prohibido.
- [ ] **Escala 2024-2025:** procesar 48 particiones solo despues de aprobar 03_01 y 04.
- [ ] **05 Municipio y periodo:** pendiente de geografia canonica y consolidacion diaria.

Referencias:
[`../temperature_daily_processing.md`](../temperature_daily_processing.md) y
[`../climate_audits/auditoria_temperatura_2024_2025.md`](../climate_audits/auditoria_temperatura_2024_2025.md).

