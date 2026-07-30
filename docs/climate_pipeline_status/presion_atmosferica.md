# Estado del pipeline: presión atmosférica

**Actualizado:** 29 de julio de 2026
**Estado:** ciclo 01–07 completo
**Fuente:** `62tk-nxj5`
**Alcance:** Boyacá y Cundinamarca, 2024–2025

- [X] **01 Crudo:** 48 de 48 particiones cerradas; no fue necesario descargar.
- [X] **02 Auditoría cruda:** 1.641 archivos y 1.620.915 filas inventariadas; muestra contigua de 190.792 filas.
- [X] **Contrato:** sensor `0255`, unidad hPa, rango operativo 400–1.100 y media diaria.
- [X] **03 Diario por sensor:** 48 particiones completas con `escalar_meteorologico_diario_v1`.
- [X] **04 Auditoría diaria:** 27.782 filas estación-sensor-día auditadas; las alertas usan etiquetas genéricas de valor y amplitud.
- [X] **05 Curado por estación:** consolidación `cierre_presion_atmosferica_2024_2025_v1`.
- [X] **06 Geografía:** fuentes oficiales; 31 asignaciones canónicas en Boyacá y 42 en Cundinamarca.
- [X] **07 Municipio diario:** calendario para los 239 municipios.
- [ ] **08 Indicadores por periodo:** pendiente de definir productos analíticos.

La auditoría identificó once estaciones con movimiento superior a 100 metros
o variación de etiquetas. Estas alertas permanecen disponibles para revisión
y no se resolvieron mediante imputación.
