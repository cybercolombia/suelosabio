# Estado del pipeline: precipitacion

**Actualizado:** 22 de julio de 2026  
**Estado:** en proceso  
**Fuente:** `s54a-sgyg`  
**Alcance objetivo:** Boyaca y Cundinamarca, enero de 2024 a diciembre de 2025

## Resumen ejecutivo

El contrato diario de precipitacion fue validado de extremo a extremo en cuatro
particiones piloto: enero y febrero de 2025 para ambos departamentos. Las
**48 particiones mensuales** del objetivo 2024-2025 terminaron el paso 03 y
producen 42.190 filas estacion-sensor-dia. Los pasos 04 y 05 deben cerrarse
ahora sobre las 48 antes de pasar a municipio.

## 01. Descarga cruda

**Estado de etapa:** `[P]` disponible estructuralmente; integridad final pendiente.

- [X] Fuente oficial seleccionada: `s54a-sgyg`.
- [X] Alcance territorial fijado en Boyaca y Cundinamarca.
- [X] Carpetas mensuales presentes para 2024 y 2025 en ambos departamentos.
- [X] Los crudos se conservan inmutables en `clima_crudo`.
- [ ] Reconciliar partes consecutivas y ultimo lote de las 48 particiones.
- [ ] Confirmar fechas internas y ausencia de archivos incompletos en todo el alcance.
- [ ] Publicar un resumen final de filas, bytes y manifiestos de descarga.

## 02. Auditoria de datos crudos

**Estado de etapa:** `[X]` evidencia aprobada para escalar 2024-2025.

- [X] Auditados 2021, 2023 y 2025 en ambos departamentos.
- [X] Auditadas muestras estratificadas de los doce meses de 2024 en ambos departamentos.
- [X] Identificados duplicados exactos, cadencias de 2, 10 y 60 minutos y sensores paralelos.
- [X] Confirmada la ausencia transversal del 5 al 25 de febrero de 2025.
- [X] Identificado el patron instrumental sospechoso `0035215030` / `0240`.
- [X] Confirmadas tambien cadencias de 1 minuto en 2024, ya admitidas por el contrato.
- [X] Comparado 2024 contra los patrones que sustentan el contrato vigente.
- [X] Publicada la sintesis de cierre de la auditoria cruda de 2024.

Evidencia:

- [`../climate_audits/02_datos_crudos/auditoria_precipitacion_boyaca_2021_2023.md`](../climate_audits/02_datos_crudos/auditoria_precipitacion_boyaca_2021_2023.md)
- [`../climate_audits/02_datos_crudos/auditoria_precipitacion_boyaca_2025.md`](../climate_audits/02_datos_crudos/auditoria_precipitacion_boyaca_2025.md)
- [`../climate_audits/02_datos_crudos/auditoria_precipitacion_cundinamarca_2021_2023.md`](../climate_audits/02_datos_crudos/auditoria_precipitacion_cundinamarca_2021_2023.md)
- [`../climate_audits/02_datos_crudos/auditoria_precipitacion_cundinamarca_2025.md`](../climate_audits/02_datos_crudos/auditoria_precipitacion_cundinamarca_2025.md)
- [`../climate_audits/02_datos_crudos/auditoria_precipitacion_2024.md`](../climate_audits/02_datos_crudos/auditoria_precipitacion_2024.md)
- [`../climate_audits/transversales/alerta_cobertura_febrero_2025.md`](../climate_audits/transversales/alerta_cobertura_febrero_2025.md)

## Contrato de variable

**Estado de etapa:** `[X]` validado para el piloto.

- [X] `PrecipitationRules.py` define fuente, unidad, sensores y columnas.
- [X] Los valores se interpretan como incrementos del intervalo y se suman por dia.
- [X] Duplicados exactos y repeticiones equivalentes se eliminan con trazabilidad.
- [X] Conflictos de una misma clave se excluyen; no se promedian.
- [X] Valores negativos y filas incompatibles se rechazan y exportan.
- [X] Las reglas cuentan con pruebas automatizadas.
- [ ] Reabrir el contrato solo si la auditoria 2024 descubre un patron no cubierto.

## 03. Diario por estacion y sensor

**Estado de etapa:** `[X]` 48 de 48 particiones objetivo terminadas.

- [X] Boyaca 2025-01: manifiesto `COMPLETA`.
- [X] Boyaca 2025-02: manifiesto `COMPLETA`.
- [X] Cundinamarca 2025-01: manifiesto `COMPLETA`.
- [X] Cundinamarca 2025-02: manifiesto `COMPLETA`.
- [X] Procesadas las 24 particiones de 2024.
- [X] Procesadas las 20 particiones restantes de 2025.
- [X] Reconciliados exactamente 48 manifiestos `COMPLETA`, sin faltantes ni duplicados.
- [X] Verificados 42.190 registros diarios declarados por los manifiestos.
- [X] Las cuatro particiones piloto conservan el commit `75b24d9`; las 44 nuevas usan `9dff0aa`.
- [ ] Resumir globalmente balances, rechazos, duplicados y conflictos durante el cierre de 04.

No se imputan dias ni observaciones en este paso. Las salidas viven en
`clima_diario_sensor/variable=precipitacion/fuente=s54a-sgyg/`.

## 04. Auditoria diaria

**Estado de etapa:** `[P]` piloto validado; auditoria de cierre pendiente.

- [X] Auditadas las cuatro particiones piloto de enero-febrero de 2025.
- [X] Calendario materializado con ausencias como `NaN`, no como cero.
- [X] Evaluadas cobertura, cadencia, extremos y concordancia de sensores paralelos.
- [X] Ventana piloto de cobertura definida entre 90 % y 102 %.
- [X] Implementado el catalogo esperado por intervalo activo en `auditoria_precipitacion_diaria_v2`.
- [ ] Auditar las 48 particiones procesadas del objetivo 2024-2025.
- [ ] Ejecutar y revisar el catalogo esperado de estaciones-sensores usando ambos anos.
- [ ] Detectar estaciones-sensores ausentes durante meses completos.
- [ ] Resumir cobertura, brecha maxima, extremos y discrepancias por particion.
- [ ] Aprobar o versionar de nuevo las reglas antes de consolidar a escala.

Evidencia del piloto:
[`../climate_audits/04_series_diarias/auditoria_piloto_diario_precipitacion_2025.md`](../climate_audits/04_series_diarias/auditoria_piloto_diario_precipitacion_2025.md).

## 05. Consolidacion diaria por estacion

**Estado de etapa:** `[P]` piloto validado; escala pendiente.

- [X] Consolidado enero-febrero de 2025 para ambos departamentos.
- [X] Llave unica `estacion + dia` verificada en 5.198 filas piloto.
- [X] Ausencias, baja cobertura, cuarentenas y desacuerdos conservan `NaN`.
- [X] Sensores paralelos no se suman ni se promedian.
- [X] Sensor `0035215030` / `0240` puesto en cuarentena en el piloto.
- [ ] Consolidar las 48 particiones una vez aprobada la auditoria diaria de cierre.
- [ ] Reconciliar calidad, procedencia y unicidad de toda la capa curada.
- [ ] Publicar manifiesto y reporte de cierre 2024-2025.

Contrato y resultado piloto:
[`../climate_daily_consolidation.md`](../climate_daily_consolidation.md).

## 06. Municipio y periodo

**Estado de etapa:** `[ ]` no iniciado.

- [ ] Construir el catalogo canonico estacion-municipio con DIVIPOLA.
- [ ] Definir la agregacion de estaciones a municipio sin ponderar la frecuencia subdiaria.
- [ ] Producir precipitacion municipio-dia con cobertura y numero de estaciones.
- [ ] Definir indicadores por periodo agricola: acumulado, dias con lluvia, intensidad y brechas.
- [ ] Conservar `NaN` cuando la cobertura sea insuficiente; no extrapolar acumulados.

## Siguiente bloque recomendado

1. Ejecutar 04 sobre todo 2024-2025 con la auditoria `v2`.
2. Revisar catalogo, ausencias mensuales, cobertura, extremos y sensores.
3. Versionar reglas si aparece un problema no cubierto.
4. Ejecutar 05 a escala solo despues de aprobar la evidencia de cierre.

## Plan de ejecucion del paso 03

Los cuatro bloques tienen volumen semejante y no se solapan. Enero y febrero de
2025 no se incluyen porque sus cuatro particiones piloto ya estan `COMPLETA`.

| Estado | Worker sugerido | Departamento | Ano | Meses | Particiones | Filas crudas aproximadas |
|---|---|---|---:|---|---:|---:|
| `[X]` | `w_precip_boyaca_2024` | Boyaca | 2024 | 1-12 | 12 | 1.716.496 |
| `[X]` | `w_precip_cundinamarca_2024` | Cundinamarca | 2024 | 1-12 | 12 | 1.866.195 |
| `[X]` | `w_precip_boyaca_2025_m03_m12` | Boyaca | 2025 | 3-12 | 10 | 1.919.746 |
| `[X]` | `w_precip_cundinamarca_2025_m03_m12` | Cundinamarca | 2025 | 3-12 | 10 | 1.916.182 |

Configuracion comun: `MAX_PARTICIONES=None`,
`SOBRESCRIBIR_RESULTADOS=False` y primero
`EJECUTAR_PROCESAMIENTO=False` para revisar el plan. Cada cuenta cambia despues
la bandera a `True`, reejecuta la celda de configuracion para actualizar el
valor en memoria y finalmente ejecuta la celda protegida.
