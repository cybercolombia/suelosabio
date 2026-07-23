# Consolidacion diaria de precipitacion

El notebook `05_ClimateDailyConsolidator.ipynb` transforma el calendario
auditado en una capa canonica preliminar con una fila por estacion y dia. No
modifica `clima_crudo`, `clima_diario_sensor` ni los productos de auditoria.

## Alcance de esta version

La primera ejecucion usa los cuatro pilotos de enero y febrero de 2025. Su
objetivo es validar las reglas antes de procesar 2021-2025.

```python
AUDITORIA_NOMBRE = 'piloto_2025_01_02'
CONSOLIDACION_NOMBRE = 'piloto_2025_01_02_v1'

COBERTURA_MINIMA_PCT = 90.0
COBERTURA_MAXIMA_PCT = 102.0
TOLERANCIA_SENSORES_MM = 0.1
PRIORIDAD_SENSORES = ['0240', '0257']
MINIMO_DIAS_CUARENTENA = 3
```

Estos parametros forman parte del contrato
`precipitacion_estacion_dia_v1`. Si cambia alguno, debe usarse otro nombre de
consolidacion y conservar el manifiesto anterior.

## Reglas de precipitacion

- Un dia sin observacion conserva `precipitacion_diaria_mm=NaN`.
- Un cero observado puede ser aceptado; ausencia y cero no son equivalentes.
- Un sensor solo es candidato cuando su cobertura esta entre 90 % y 102 %.
- Tres o mas dias con el patron `POSITIVOS_PERSISTENTES` ponen el sensor en
  cuarentena para el periodo procesado.
- Un extremo aislado se conserva y mantiene `requiere_revision=True`.
- Los sensores paralelos nunca se suman ni se promedian.
- Si varios sensores validos difieren mas de 0,1 mm, el valor aceptado queda en
  `NaN` con calidad `SENSORES_DISCREPANTES`.
- Si concuerdan, se selecciona primero `0240`, despues `0257` y luego cualquier
  otro sensor disponible.

La prioridad de sensores y la suma diaria son especificas de precipitacion. El
calendario, los manifiestos, las escrituras atomicas y la trazabilidad son piezas
reutilizables para otras variables.

## Entrada

```text
eco2026_processed/auditorias_clima_diario/
  variable=precipitacion/
    fuente=s54a-sgyg/
      auditoria=piloto_2025_01_02/
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
      consolidacion=piloto_2025_01_02_v1/
        departamento=BOYACÁ/anio=2025/mes=01/
          observaciones_estacion_dia.parquet
        departamento=BOYACÁ/anio=2025/mes=02/
          observaciones_estacion_dia.parquet
        departamento=CUNDINAMARCA/anio=2025/mes=01/
          observaciones_estacion_dia.parquet
        departamento=CUNDINAMARCA/anio=2025/mes=02/
          observaciones_estacion_dia.parquet
        candidatos_sensor.parquet
        sensores_cuarentena.parquet
        resumen_calidad.parquet
        ConsolidacionDiaria_precipitacion_piloto_2025_01_02_v1.md
        manifest.json
        figures/
```

La salida principal conserva sensor seleccionado, sensores observados y validos,
cobertura, diferencia entre sensores, calidad, motivo, geografia observada y
regla aplicada.

## Ejecucion segura

1. Ejecutar inicialmente con `EJECUTAR_CONSOLIDACION=False`.
2. Confirmar que la auditoria de entrada aparezca `COMPLETA`.
3. Cambiar `EJECUTAR_CONSOLIDACION=True`.
4. Mantener `GUARDAR_RESULTADOS=True` y
   `SOBRESCRIBIR_CONSOLIDACION=False`.
5. Ejecutar nuevamente desde la configuracion hasta el final.
6. Revisar el manifiesto, el resumen de calidad y la cuarentena.
7. Volver a dejar la bandera de ejecucion en `False` antes de guardar.

## Resultado validado del piloto

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
174 mm. El piloto queda listo para preparar el procesamiento historico antes del
agregado municipal.
