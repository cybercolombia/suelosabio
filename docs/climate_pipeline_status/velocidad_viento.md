# Estado del pipeline: velocidad del viento

**Actualizado:** 29 de julio de 2026
**Estado:** ciclo 01–07 completo
**Fuente:** `sgfv-3yp8`
**Alcance:** Boyacá y Cundinamarca, 2024–2025

- [X] **01 Crudo:** 48 de 48 particiones cerradas; no fue necesario descargar.
- [X] **02 Auditoría cruda:** 4.901 archivos y 4.877.266 filas inventariadas; muestra contigua de 191.193 filas.
- [X] **Contrato:** sensor `0103`, unidad m/s, rango operativo 0–100 y media diaria.
- [X] **03 Diario por sensor:** 48 particiones completas con `escalar_meteorologico_diario_v1`.
- [X] **04 Auditoría diaria:** 29.708 filas estación-sensor-día auditadas; extremos y amplitudes permanecen como alertas.
- [X] **05 Curado por estación:** consolidación `cierre_velocidad_viento_2024_2025_v1`.
- [X] **06 Geografía:** fuentes oficiales; 33 asignaciones canónicas en Boyacá y 46 en Cundinamarca.
- [X] **07 Municipio diario:** calendario para los 239 municipios.
- [ ] **08 Indicadores por periodo:** pendiente de definir productos analíticos.

La auditoría cruda identificó doce estaciones con movimiento superior a 100
metros o variación de etiquetas. No se imputaron valores ni se promediaron
sensores discrepantes.
