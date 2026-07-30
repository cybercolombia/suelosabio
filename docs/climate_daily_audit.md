# Auditoria de la capa diaria de precipitacion

El notebook `04_Climate_Precipitation_DailyAudit.ipynb` audita las salidas preliminares de
`03_Climate_Precipitation_DailyProcessor.ipynb`. Es una etapa de solo lectura: no modifica los
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
- Catalogo de estaciones-sensores con primer y ultimo mes observado.
- Actividad mensual esperada dentro del intervalo observado de cada par.
- Meses completamente ausentes entre la primera y ultima aparicion del par.
- Dias observados y ausentes sin reemplazar `NaN` por cero.
- Fechas observadas minima y maxima por estacion-sensor.
- Cobertura diaria frente al umbral candidato.
- Coberturas superiores a la tolerancia configurada para revision de cadencia.
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
        catalogo_estacion_sensor.parquet
        actividad_mensual_estacion_sensor.parquet
        ausencias_mes_completo.parquet
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
3. Cambiar `EJECUTAR_AUDITORIA_DIARIA=True` y reejecutar la celda de
   configuracion para actualizar la bandera en memoria.
4. Ejecutar la celda final protegida.
5. Mantener `GUARDAR_RESULTADOS=True` para exportar la evidencia.
6. Revisar el Markdown, los Parquet y las figuras antes de decidir reglas.
7. Volver a dejar la bandera de ejecucion en `False` antes de guardar el notebook.

## Limites deliberados

Esta version no calcula todavia rachas secas ni resuelve geografia canonica. El
catalogo considera esperado un par solo entre su primer y ultimo mes observado:
detecta huecos mensuales internos, pero no puede demostrar si debio existir
antes del alta o despues de la ultima aparicion. Tampoco llena
`precipitacion_diaria_mm`: esa columna debe permanecer en `NaN` hasta aprobar
las reglas que aplicara el notebook 05.

La implementacion de esas reglas y su operacion segura se documentan en
[`climate_daily_consolidation.md`](climate_daily_consolidation.md).

## Visualizacion interactiva

El final del notebook incluye una celda opcional con Plotly. Permite escoger un
par estacion-sensor y recorrer toda su serie con zoom, desplazamiento, botones
de rango y control inferior de fechas.

```python
EJECUTAR_GRAFICA_INTERACTIVA = True
GRAFICA_USAR_RESULTADO_EN_MEMORIA = False
GRAFICA_DEPARTAMENTO = 'CUNDINAMARCA'
GRAFICA_ESTACION = '3505500121'
GRAFICA_SENSOR = '0240'
```

Con `GRAFICA_USAR_RESULTADO_EN_MEMORIA=False`, la vista evita resultados viejos
del runtime y lee la auditoria indicada por `AUDIT_OUTPUT_DIR`.

La figura superior muestra solamente valores observados y mantiene los huecos.
La franja inferior distingue dias observados y ausentes; un punto ausente nunca
se dibuja como lluvia cero. Si la auditoria no esta cargada en memoria, la celda
lee `calendario_estacion_sensor.parquet` de `AUDIT_OUTPUT_DIR`.

La visualizacion es diagnostica. No agrega estaciones, no selecciona sensores y
no modifica ningun Parquet.
