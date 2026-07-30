# Estado del pipeline: temperatura ambiente

**Actualizado:** 29 de julio de 2026
**Estado:** piloto v2 pendiente de repeticion
**Fuente:** `sbwg-7ju4`  
**Alcance objetivo:** Boyaca y Cundinamarca, 2024-2025

- [P] **01 Crudo:** las 48 particiones de 2024-2025 fueron observadas estructuralmente; falta reconciliacion integral de lotes y fechas internas.
- [X] **02 Auditoria cruda:** ambos departamentos y ambos anos tienen evidencia; deben conservarse febrero de 2025 y meses contrastantes como pruebas de cobertura.
- [P] **Contrato:** la v1 valido estadisticos y trazabilidad, pero mezclaba saltos entre dias con cadencia. `temperatura_diaria_v2` corrige esa inferencia y deja frecuencias desconocidas como no evaluables.
- [P] **03 Diario por sensor:** cuatro particiones v1 terminaron `COMPLETA`; deben sobrescribirse enero-febrero de 2025, ambos departamentos, con la v2.
- [P] **04 Auditoria diaria:** la v1 confirmo el hueco del 5 al 25 de febrero y detecto el error de cadencia. `auditoria_temperatura_diaria_v2` esta implementada y pendiente de corrida.
- [ ] **05 Curado por estacion:** disenar reglas termicas a partir del piloto; el consolidador de precipitacion esta prohibido.
- [ ] **Escala 2024-2025:** bloqueada hasta aprobar la repeticion v2 de 03-04 y un piloto de 05.
- [ ] **06 Geografia:** pendiente de consolidacion diaria para conocer su catalogo de estaciones.
- [ ] **07 Municipio diario:** pendiente.
- [ ] **08 Indicadores por periodo:** pendiente.

Referencias:
[`../temperature_daily_processing.md`](../temperature_daily_processing.md) y
[`../climate_audits/04_series_diarias/auditoria_piloto_temperatura_ambiente_2025.md`](../climate_audits/04_series_diarias/auditoria_piloto_temperatura_ambiente_2025.md).

## Siguiente paso exacto

Repetir en 03 las cuatro particiones de enero-febrero de 2025:

```python
VARIABLE_NOMBRE = 'temperatura_ambiente'
DATASET_ID = 'sbwg-7ju4'
PROCESAR_DEPARTAMENTOS = ['BOYACÁ', 'CUNDINAMARCA']
PROCESAR_ANIOS = [2025]
PROCESAR_MESES = [1, 2]
MAX_PARTICIONES = None
SOBRESCRIBIR_RESULTADOS = True
EJECUTAR_PROCESAMIENTO = True
```

`SOBRESCRIBIR_RESULTADOS=True` se limita a esas cuatro salidas piloto y es
necesario porque reemplazan artefactos v1. Antes de ejecutar, el plan debe
mostrar cuatro particiones y `temperatura_diaria_v2`; al terminar, los cuatro
manifiestos deben quedar `COMPLETA`.

Luego ejecutar 04 con:

```python
VARIABLE_NOMBRE = 'temperatura_ambiente'
DATASET_ID = 'sbwg-7ju4'
AUDITAR_DEPARTAMENTOS = ['BOYACÁ', 'CUNDINAMARCA']
AUDITAR_ANIOS = [2025]
AUDITAR_MESES = [1, 2]
AUDITORIA_NOMBRE = 'piloto_temperatura_ambiente_2025_01_02_v2'
SOBRESCRIBIR_AUDITORIA = False
EJECUTAR_AUDITORIA_DIARIA = True
```

Detenerse despues de exportar 04. La siguiente tarea de desarrollo es analizar
esa evidencia y crear una consolidacion termica 05; no escalar ni usar la
consolidacion de precipitacion.
