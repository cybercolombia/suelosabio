# Estado del pipeline: temperatura mínima

**Actualizado:** 29 de julio de 2026
**Estado:** ciclo 01–07 completo
**Fuente:** `afdg-3zpb`
**Alcance:** Boyacá y Cundinamarca, 2024–2025

- [X] **01 Crudo:** 48 de 48 particiones cerradas; no fue necesario descargar.
- [X] **02 Auditoría cruda:** 747 archivos y 718.097 filas revisadas; muestra de 165.377 filas, sin claves duplicadas con valores en conflicto.
- [X] **03 Diario por sensor:** 48 particiones completas con `temperatura_diaria_v2`.
- [X] **04 Auditoría diaria:** 25.120 filas estación-sensor-día auditadas.
- [X] **05 Curado por estación:** consolidación `cierre_temperatura_minima_2024_2025_v1`.
- [X] **06 Geografía:** catálogo oficial de estaciones, DIVIPOLA y polígonos municipales; 34 asignaciones canónicas en Boyacá y 37 en Cundinamarca.
- [X] **07 Municipio diario:** calendario para los 239 municipios, conservando los días sin red o sin observación como ausencia y no como cero.
- [ ] **08 Indicadores por periodo:** pendiente de definir productos analíticos.

Las alertas de movimiento de coordenadas y cobertura permanecen en los
artefactos de auditoría. No se imputaron valores.
