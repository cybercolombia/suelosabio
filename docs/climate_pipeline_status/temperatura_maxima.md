# Estado del pipeline: temperatura máxima

**Actualizado:** 29 de julio de 2026
**Estado:** ciclo 01–07 completo
**Fuente:** `ccvq-rp9s`
**Alcance:** Boyacá y Cundinamarca, 2024–2025

- [X] **01 Crudo:** 48 de 48 particiones cerradas; no fue necesario descargar.
- [X] **02 Auditoría cruda:** 738 archivos y 713.806 filas revisadas; muestra de 161.473 filas. Se detectaron cuatro claves con valores en conflicto.
- [X] **03 Diario por sensor:** 48 particiones completas con `temperatura_diaria_v2`; los conflictos se excluyeron sin promediarlos.
- [X] **04 Auditoría diaria:** 24.961 filas estación-sensor-día auditadas.
- [X] **05 Curado por estación:** consolidación `cierre_temperatura_maxima_2024_2025_v1`.
- [X] **06 Geografía:** catálogo oficial de estaciones, DIVIPOLA y polígonos municipales; 34 asignaciones canónicas en Boyacá y 37 en Cundinamarca.
- [X] **07 Municipio diario:** calendario para los 239 municipios, conservando ausencia y diagnósticos de cobertura.
- [ ] **08 Indicadores por periodo:** pendiente de definir productos analíticos.

Los cuatro conflictos crudos y las alertas geográficas permanecen trazables en
las salidas de auditoría. No se imputaron valores.
