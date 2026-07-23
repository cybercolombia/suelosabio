# Auditoria de la capa diaria de precipitacion

El notebook `04_ClimateDailyAudit.ipynb` audita las salidas preliminares de
`03_ClimateDailyProcessor.ipynb`. Es una etapa de solo lectura: no modifica los
Parquet diarios, no imputa ausencias, no elimina extremos y no selecciona un
sensor canonico.

## Entrada predeterminada

La primera corrida compara los cuatro pilotos:

```python
AUDITAR_DEPARTAMENTOS = ['CUNDINAMARCA', 'BOYACÁ']
AUDITAR_ANIOS = [2025]
AUDITAR_MESES = [1, 2]
AUDITORIA_NOMBRE = 'piloto_2025_01_02'
```

Cada particion debe contener `manifest.json` en estado `COMPLETA` y
`observaciones_diarias.parquet`. El notebook comprueba que las filas coincidan
con el manifiesto antes de concatenarlas.

## Parametros diagnosticos

```python
UMBRAL_COBERTURA_CANDIDATO_PCT = 90.0
UMBRAL_TOTAL_EXTREMO_MM = 200.0
UMBRAL_INTERVALO_SOSPECHOSO_MM = 25.0
TOLERANCIA_SENSORES_MM = 0.1
```

Estos valores sirven para producir listas de revision. No son reglas de limpieza
ni implican que un dia sea valido o invalido. Cambiarlos requiere conservar el
manifiesto y el nombre de la nueva auditoria.

## Analisis producidos

- Calendario completo por departamento, estacion, sensor y mes.
- Dias observados y ausentes sin reemplazar `NaN` por cero.
- Fechas observadas minima y maxima por estacion-sensor.
- Cobertura diaria frente al umbral candidato.
- Coberturas superiores a 100 % para revision de cadencia.
- Totales diarios, intervalos altos y extremos p99 candidatos para revision.
- Patrones con observaciones positivas persistentes.
- Comparacion de sensores paralelos por fecha y tolerancia.
- Resumen de concordancia, diferencias y correlacion entre sensores.

Los motivos pueden coincidir en una misma fila. Por ejemplo, una observacion
puede ser simultaneamente extrema, tener un intervalo alto y presentar un patron
positivo persistente. Ningun motivo elimina la fila.

## Productos

```text
eco2026_processed/auditorias_clima_diario/
  variable=precipitacion/
    fuente=s54a-sgyg/
      auditoria=piloto_2025_01_02/
        calendario_estacion_sensor.parquet
        resumen_particiones.parquet
        resumen_estacion_sensor.parquet
        valores_sospechosos.parquet
        comparaciones_sensores.parquet
        resumen_sensores_paralelos.parquet
        AuditoriaDiaria_precipitacion_piloto_2025_01_02.md
        manifest.json
        figures/
```

El manifiesto final registra commit, procedencia, parametros, tiempos, metricas
y rutas. Si la carpeta contiene una auditoria `COMPLETA`, una repeticion no la
sobrescribe. Una salida incompleta exige revision antes de habilitar
`SOBRESCRIBIR_AUDITORIA=True`.

## Ejecucion segura

1. Ejecutar las celdas hasta revisar que las cuatro entradas esten `COMPLETA`.
2. Confirmar que `AUDIT_OUTPUT_DIR` apunta a la carpeta compartida esperada.
3. Cambiar `EJECUTAR_AUDITORIA_DIARIA=True`.
4. Mantener `GUARDAR_RESULTADOS=True` para exportar la evidencia.
5. Revisar el Markdown, los Parquet y las figuras antes de decidir reglas.
6. Volver a dejar la bandera de ejecucion en `False` antes de guardar el notebook.

## Limites deliberados

Esta version no calcula todavia rachas secas, no resuelve geografia canonica y
no decide si una estacion estuvo activa durante todo el mes. Tampoco llena
`precipitacion_diaria_mm`: esa columna debe permanecer en `NaN` hasta aprobar las
reglas que aplicara el notebook 05.

La implementacion de esas reglas y su operacion segura se documentan en
[`climate_daily_consolidation.md`](climate_daily_consolidation.md).
