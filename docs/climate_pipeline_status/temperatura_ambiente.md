# Estado del pipeline: temperatura ambiente

**Actualizado:** 29 de julio de 2026
**Estado:** ciclo 01–07 completo
**Fuente:** `sbwg-7ju4`
**Alcance:** Boyacá y Cundinamarca, 2024–2025

- [X] **01 Crudo:** 48 de 48 particiones cerradas; no fue necesario descargar.
- [X] **02 Auditoría cruda:** 2.477 archivos y 2.452.584 filas inventariadas; muestra contigua de 190.969 filas.
- [X] **Contrato:** media diaria con `temperatura_diaria_v2`; la cadencia se infiere dentro de cada día.
- [X] **03 Diario por sensor:** 48 particiones completas con la regla v2.
- [X] **04 Auditoría diaria:** 31.966 filas estación-sensor-día auditadas.
- [X] **05 Curado por estación:** consolidación `cierre_temperatura_ambiente_2024_2025_v1`.
- [X] **06 Geografía:** fuentes oficiales; 35 asignaciones canónicas en Boyacá y 47 en Cundinamarca.
- [X] **07 Municipio diario:** calendario para los 239 municipios, sin convertir ausencias en cero.
- [ ] **08 Indicadores por periodo:** pendiente de definir productos analíticos.

La auditoría cruda conservó doce estaciones con movimiento superior a 100
metros o variación de etiquetas. La auditoría diaria mantiene alertas de
amplitud, extremos y cobertura para revisión; no se imputaron valores.
