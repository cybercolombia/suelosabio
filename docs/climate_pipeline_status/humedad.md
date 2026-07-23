# Estado del pipeline: humedad

**Actualizado:** 22 de julio de 2026  
**Estado:** bloqueada antes de 03  
**Fuente:** `uext-mhny`  
**Alcance objetivo:** Boyaca y Cundinamarca, 2024-2025

- [P] **01 Crudo:** estructura 2021-2025 presente para ambos departamentos; falta reconciliacion integral.
- [P] **02 Auditoria cruda:** Cundinamarca 2025 auditada; faltan Boyaca, evidencia de 2024 y contraste de febrero de 2025.
- [ ] **Contrato:** `HumidityRules.py` es un marcador bloqueante, no una regla implementada.
- [ ] **03 Diario por sensor:** bloqueado hasta definir unidad, rango, estadistico, duplicados, conflictos y cobertura.
- [ ] **04 Auditoria diaria:** `HumidityDailyAudit.py` bloquea la ejecucion hasta contar con contrato y piloto de 03.
- [ ] **05 Curado por estacion:** pendiente de evidencia diaria.
- [ ] **Escala 2024-2025:** no autorizada.
- [ ] **06 Municipio y periodo:** pendiente.

Siguiente paso: completar 02 en ambos departamentos y anos objetivo, redactar el
contrato de humedad, agregar pruebas y ejecutar un piloto de enero-febrero de
2025. Evidencia disponible:
[`../climate_audits/02_datos_crudos/auditoria_humedad_cundinamarca_2025.md`](../climate_audits/02_datos_crudos/auditoria_humedad_cundinamarca_2025.md).
