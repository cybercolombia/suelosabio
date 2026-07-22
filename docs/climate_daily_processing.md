# Procesamiento diario de precipitacion

Este documento describe el piloto del notebook
`notebooks/ClimatePipeline/03_ClimateDailyProcessor.ipynb`. Su objetivo es
transformar una particion mensual de precipitacion subdiaria en observaciones por
estacion, sensor y dia, sin modificar `clima_crudo`.

El procesador todavia no esta habilitado para ejecutar todo el historico. Primero
deben revisarse cuatro particiones piloto con el notebook de auditoria diaria.

## Contrato preliminar

La regla `precipitacion_incremental_v1` aplica estas decisiones:

- La fuente admitida es `s54a-sgyg` y la unidad debe ser `mm`.
- `valorobservado` se interpreta provisionalmente como incremento del intervalo.
- Se eliminan duplicados exactos y claves repetidas con el mismo valor.
- Una clave `estacion + sensor + timestamp` con valores diferentes se excluye y
  se conserva en `conflictos.parquet`.
- Los valores negativos, fechas invalidas o fuera de la particion y filas de otra
  fuente, departamento, unidad o variable se conservan en `rechazados.parquet`.
- La cadencia se infiere por estacion y sensor dentro de cada mes.
- Los sensores paralelos nunca se suman entre si.
- No se imputan observaciones subdiarias y no se eliminan extremos.

La salida distingue dos conceptos:

- `precipitacion_observada_mm`: suma de los incrementos validos disponibles.
- `precipitacion_diaria_mm`: suma aceptada para analisis; permanece en `NaN`
  hasta que la auditoria diaria apruebe una regla de cobertura.

Esto evita presentar un dia parcial como si fuera un total diario confiable.

## Carpetas y productos

Entrada de solo lectura:

```text
eco2026_processed/clima_crudo/
  variable=precipitacion/fuente=s54a-sgyg/
    departamento=CUNDINAMARCA/anio=2025/mes=02/part-*.parquet
```

Salida:

```text
eco2026_processed/clima_diario_sensor/
  variable=precipitacion/fuente=s54a-sgyg/
    departamento=CUNDINAMARCA/anio=2025/mes=02/
      observaciones_diarias.parquet
      cadencias.parquet
      duplicados_eliminados.parquet
      conflictos.parquet
      rechazados.parquet
      resumen_procesamiento.parquet
      manifest.json
```

El manifiesto pasa a `COMPLETA` solamente despues de escribir y verificar todos
los Parquet. Una interrupcion deja la particion como incompleta para que sea
revisada en lugar de mezclarse silenciosamente con otra corrida.

## Configuracion del piloto

Las variables que normalmente se modifican son:

```python
PROCESAR_DEPARTAMENTOS = ['CUNDINAMARCA']
PROCESAR_ANIOS = [2025]
PROCESAR_MESES = [2]
WORKER_ID = 'worker_a'
MAX_PARTICIONES = 1
SOBRESCRIBIR_RESULTADOS = False
EJECUTAR_PROCESAMIENTO = False
```

Secuencia segura en Colab:

1. Abrir la version actual del notebook desde la rama del equipo.
2. Ejecutar las celdas hasta visualizar el plan y confirmar entrada y salida.
3. Asignar un `WORKER_ID` que no contenga correo ni datos personales.
4. Verificar que ninguna otra cuenta tenga asignada la misma particion.
5. Cambiar `EJECUTAR_PROCESAMIENTO` a `True` y ejecutar la celda final.
6. Revisar que `manifest.json` indique `COMPLETA` y conservar el resumen.
7. Volver a dejar la bandera en `False` antes de guardar el notebook.

`SOBRESCRIBIR_RESULTADOS=False` es la opcion normal. Una particion completa se
omite al repetirla. Una particion incompleta produce un error deliberado; no se
debe activar la sobrescritura sin revisar primero por que se interrumpio.

## Pilotos requeridos

**Estado actual:** completados y comparados. El contrato fue validado despues
por 03_01 y 04; esta tabla se conserva como trazabilidad del piloto.

| Worker | Departamento | Ano | Mes | Objetivo |
|---|---|---:|---:|---|
| A | Cundinamarca | 2025 | 1 | Mes pesado y con duplicados |
| B | Cundinamarca | 2025 | 2 | Mes de menor cobertura |
| C | Boyaca | 2025 | 1 | Comparacion territorial |
| D | Boyaca | 2025 | 2 | Comparacion territorial |

La compuerta de los cuatro pilotos ya fue superada. El historico 2021-2025 puede
escalarse usando las reglas versionadas y conservando manifiestos por particion.
La auditoria `03_01_ClimateDailyAudit.ipynb` definio cobertura minima,
tratamiento de sensores paralelos y criterios para valores sospechosos. Su
configuracion y productos se describen en
[`climate_daily_audit.md`](climate_daily_audit.md).

## Verificacion local

Las reglas y el controlador se validan con:

```bash
python3 -m unittest discover -s tests -v
```

Las pruebas cubren normalizacion de rutas, escritura atomica, duplicados,
conflictos, rechazos, cadencias de uno y cinco minutos, sensores paralelos,
reanudacion y deteccion de salidas incompletas.
