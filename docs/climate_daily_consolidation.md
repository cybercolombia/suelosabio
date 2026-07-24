# Consolidacion diaria de precipitacion

El notebook `05_ClimateDailyConsolidator.ipynb` transforma el calendario
auditado en una capa canonica preliminar con una fila por estacion y dia. No
modifica `clima_crudo`, `clima_diario_sensor` ni los productos de auditoria.

## Alcance de esta version

El contrato `precipitacion_estacion_dia_v2` procesa el cierre completo de
Boyaca y Cundinamarca para 2024-2025. Usa la auditoria diaria ya materializada;
no necesita repetir la descarga, el paso 03 ni el paso 04.

```python
AUDITORIA_NOMBRE = 'cierre_precipitacion_2024_2025_v1'
CONSOLIDACION_NOMBRE = 'cierre_precipitacion_2024_2025_v2'

COBERTURA_MINIMA_PCT = 90.0
COBERTURA_MAXIMA_PCT = 102.0
TOLERANCIA_SENSORES_MM = 0.1
PRIORIDAD_SENSORES = ['0240', '0257']
MINIMO_DIAS_CUARENTENA = 3

AJUSTES_TEMPORALES = [{
    'ajuste_id': 'medina_3505500121_decimas_mm_v1',
    'departamento': 'CUNDINAMARCA',
    'codigoestacion': '3505500121',
    'codigosensor': '0240',
    'fecha_inicio': '2024-10-29',
    'fecha_fin': '2025-07-21',
    'factor_multiplicativo': 0.1,
    'motivo_ajuste': 'CAMBIO_ESCALA_DECIMAS_MM',
    'evidencia_ajuste': 'auditoria_cierre_diario_precipitacion_2024_2025',
}]
```

Estos parametros forman parte del contrato
`precipitacion_estacion_dia_v2`. Si cambia alguno, debe usarse otro nombre de
consolidacion y conservar el manifiesto anterior.

## Reglas de precipitacion

- Un dia sin observacion conserva `precipitacion_diaria_mm=NaN`.
- Un cero observado puede ser aceptado; ausencia y cero no son equivalentes.
- Un sensor solo es candidato cuando su cobertura esta entre 90 % y 102 %.
- Tres o mas dias con el patron `POSITIVOS_PERSISTENTES` ponen el sensor en
  cuarentena entre la primera y la ultima fecha de evidencia, no durante toda
  su historia.
- La ventana aprobada de `3505500121/0240` se multiplica por 0,1 porque la
  auditoria encontro evidencia de valores publicados en decimas de milimetro.
- Cada calibracion conserva valor original, valor ajustado, factor, intervalo,
  motivo, evidencia e identificador de regla.
- Un extremo aislado se conserva y mantiene `requiere_revision=True`.
- Los sensores paralelos nunca se suman ni se promedian.
- Si varios sensores validos difieren mas de 0,1 mm, el valor aceptado queda en
  `NaN` con calidad `SENSORES_DISCREPANTES`.
- Si concuerdan, se selecciona primero `0240`, despues `0257` y luego cualquier
  otro sensor disponible.

La prioridad de sensores y la suma diaria son especificas de precipitacion. El
calendario, los manifiestos, las escrituras atomicas y la trazabilidad son piezas
reutilizables para otras variables.

La calibracion vive en 05 porque opera sobre un total diario mediante una
transformacion lineal. El calendario auditado y los productos anteriores se
mantienen intactos. Humedad, temperatura, presion y viento no pueden usar este
contrato: deben definir y probar sus propias reglas antes de consolidarse.

## Entrada

```text
eco2026_processed/auditorias_clima_diario/
  variable=precipitacion/
    fuente=s54a-sgyg/
      auditoria=cierre_precipitacion_2024_2025_v1/
        calendario_estacion_sensor.parquet
        valores_sospechosos.parquet
        manifest.json
```

El manifiesto debe estar en estado `COMPLETA` y usar la version de auditoria
esperada.

## Salida

```text
eco2026_processed/clima_diario_curado/
  variable=precipitacion/
    fuente=s54a-sgyg/
      consolidacion=cierre_precipitacion_2024_2025_v2/
        departamento=BOYACÁ/anio=2024/mes=01/
          observaciones_estacion_dia.parquet
        ...
        departamento=CUNDINAMARCA/anio=2025/mes=12/
          observaciones_estacion_dia.parquet
        candidatos_sensor.parquet
        sensores_cuarentena.parquet
        ajustes_temporales.parquet
        resumen_calidad.parquet
        ConsolidacionDiaria_precipitacion_cierre_precipitacion_2024_2025_v2.md
        manifest.json
        figures/
```

La salida principal conserva sensor seleccionado, sensores observados y validos,
cobertura, diferencia entre sensores, valor original, valor ajustado, calidad,
motivo, geografia observada y regla aplicada.

## Ausencia, descarte y cuarentena

Los tres casos producen `precipitacion_diaria_mm=NaN`, pero no significan lo
mismo:

| Caso | Motivo trazable | Evidencia conservada |
|---|---|---|
| No hubo medicion | `SIN_OBSERVACION` | Fila de calendario y fecha esperada |
| Hubo medicion incompleta | `COBERTURA_BAJA` o `COBERTURA_NO_EVALUABLE` | Valor diario preliminar y cobertura |
| Hubo medicion no confiable | `SENSOR_CUARENTENA` | Original en calendario y candidatos, ventana y motivo en cuarentena |

`clima_crudo`, `clima_diario_sensor` y la auditoria diaria nunca se modifican.
La cuarentena no borra datos: evita que un valor dudoso se convierta en el valor
canonico aceptado.

## Ejecucion segura

1. Ejecutar inicialmente con `EJECUTAR_CONSOLIDACION=False`.
2. Confirmar que la auditoria de entrada aparezca `COMPLETA`.
3. Cambiar `EJECUTAR_CONSOLIDACION=True`.
4. Mantener `GUARDAR_RESULTADOS=True` y
   `SOBRESCRIBIR_CONSOLIDACION=False`.
5. Ejecutar nuevamente desde la configuracion hasta el final.
6. Revisar el manifiesto, el resumen de calidad y la cuarentena.
7. Volver a dejar la bandera de ejecucion en `False` antes de guardar.

## Resultado historico del piloto v1

La ejecucion en Colab del 21 de julio de 2026, con el commit `2022486`, termino
en estado `COMPLETA` en 38,4 segundos y reprodujo la validacion local:

- 5.198 filas estacion-dia.
- 2.492 dias con precipitacion aceptada.
- 2.287 dias sin observacion.
- 412 dias observados sin sensor valido.
- Siete dias con sensores discrepantes.
- Un sensor en cuarentena: `0035215030`/`0240`.

Las 5.198 llaves estacion-dia son unicas. Ninguna ausencia, discrepancia ni fila
del sensor en cuarentena recibio precipitacion aceptada; el maximo aceptado fue
174 mm. Este resultado sustento la estructura de 05, pero no reemplaza la
ejecucion de cierre v2.

## Compuerta de cierre v2

Antes de entregar la capa a 06 se debe comprobar:

1. Las llaves `departamento + estacion + fecha` son unicas.
2. La calibracion solo afecta `3505500121/0240` entre el 29 de octubre de 2024
   y el 21 de julio de 2025.
3. Fuera de esa ventana, el valor original y el ajustado coinciden.
4. Las ventanas en cuarentena quedan en `NaN` y los periodos confiables del
   mismo sensor sobreviven.
5. Ausencias, cobertura insuficiente y discrepancias conservan motivos distintos.
6. El manifiesto enumera las reglas, particiones, metricas y archivos generados.
