# Auditoria piloto del procesamiento diario de precipitacion

> **Estado:** evidencia historica de la compuerta 04. Las reglas propuestas
> aqui ya fueron implementadas y validadas por 05. Consulte
> [`../../climate_daily_consolidation.md`](../../climate_daily_consolidation.md) para el
> contrato vigente y sus resultados.

Este reporte compara las cuatro particiones piloto producidas por
`03_ClimateDailyProcessor.ipynb`. Los resultados locales provienen del commit
`75b24d9` y de tres workers independientes. Todos los manifiestos terminaron en
estado `COMPLETA`.

## Alcance

| Departamento | Mes | Worker | Archivos de entrada | Filas de entrada | Filas diarias | Duracion |
|---|---:|---|---:|---:|---:|---:|
| Boyaca | 1 | `w_adriblue` | 357 | 356.908 | 1.431 | 24,16 s |
| Boyaca | 2 | `w_adrilila` | 35 | 34.862 | 193 | 10,66 s |
| Cundinamarca | 1 | `w_adrirose` | 351 | 350.584 | 1.187 | 25,37 s |
| Cundinamarca | 2 | `w_adriblue` | 38 | 37.716 | 176 | 10,34 s |

Las ecuaciones de trazabilidad cuadran en las cuatro particiones: cada fila de
entrada queda agregada, rechazada, excluida por conflicto o eliminada como
duplicado. No se encontraron filas rechazadas, claves conflictivas ni claves
repetidas con el mismo valor pero metadatos distintos.

## Duplicacion exacta

| Departamento | Mes | Duplicados eliminados | Porcentaje de entrada |
|---|---:|---:|---:|
| Boyaca | 1 | 178.454 | 50,00 % |
| Boyaca | 2 | 8.461 | 24,27 % |
| Cundinamarca | 1 | 175.292 | 50,00 % |
| Cundinamarca | 2 | 10.106 | 26,79 % |

En enero todas las filas aparecen exactamente dos veces: el procesador conserva
una copia y elimina la otra. Febrero tambien contiene duplicacion, pero no en
toda la particion. El patron aparece en ambos departamentos y confirma que no es
una particularidad de un worker.

## Calendario observado

Enero contiene observaciones entre el 1 y el 31 en ambos departamentos. Febrero
solo contiene los dias 1 al 4 y 26 al 28; faltan por completo los dias 5 al 25.

La auditoria cruda ya habia confirmado mediante consulta directa a Socrata que
el salto enero-febrero no fue creado por las particiones locales. El piloto
diario revela ahora la forma exacta del hueco: 21 dias consecutivos ausentes en
los dos departamentos. Esos dias deben incorporarse mas adelante como calendario
explicito con `NaN`, nunca como lluvia cero.

## Cadencias y cobertura

Las cadencias modales fueron reconocidas para todos los pares estacion-sensor:

| Departamento | Mes | 2 min | 10 min | 60 min |
|---|---:|---:|---:|---:|
| Boyaca | 1 | 1 | 42 | 8 |
| Boyaca | 2 | 1 | 39 | 8 |
| Cundinamarca | 1 | 1 | 39 | 1 |
| Cundinamarca | 2 | 1 | 38 | 1 |

La mediana de cobertura de los dias presentes es 100 %. Existen dias parciales
y 21 coberturas ligeramente superiores a 100 % en enero, con maximo de 101,39 %.
Esto indica que el umbral de calidad no debe aplicarse antes de revisar cambios
de frecuencia, limites del dia y observaciones adicionales.

## Sensores paralelos

Cada departamento contiene una estacion con sensores `0240` y `0257`:

- Boyaca: estacion `0024035340`.
- Cundinamarca: estacion `3502500135`.

En muchos dias ambos sensores concuerdan, pero no siempre. Por ejemplo, en
Boyaca el 9 de enero `0240` suma 0 mm y `0257` suma 13,9 mm. Los sensores deben
permanecer separados hasta medir cobertura, concordancia y fallas por periodo.

## Valores diarios sospechosos

La estacion `0035215030`, sensor `0240`, municipio reportado `PISVA`, presenta
lecturas horarias positivas cercanas al valor repetido de 25,6 mm. Esto produce
totales observados entre aproximadamente 480 y 544 mm por dia, incluyendo 544 mm
el 28 de febrero.

El patron constante y repetido es compatible con saturacion, codigo de error o
mal funcionamiento, no con un evento que deba aceptarse automaticamente como
lluvia. El procesador hizo lo correcto al conservarlo sin borrarlo; la auditoria
diaria debe marcarlo y definir una regla trazable. Otros maximos, como 174 mm en
Medina, tambien requieren contexto, pero no muestran el mismo patron constante.

Una consulta pequena a la
[API oficial de precipitacion](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg)
confirmo que la fuente publica cada timestamp dos veces para esta estacion y
repite cada hora valores de 19,2 o 25,6 mm. La fuente identifica la estacion como
`PISBA` y el municipio como `PISVA`. Esto fortalece la hipotesis de patron
instrumental y justifica una cuarentena trazable del sensor, no una regla global
que elimine toda precipitacion alta.

## Validaciones superadas

- Las cuatro llaves `estacion + sensor + fecha` son unicas en la salida diaria.
- Los sensores paralelos permanecen separados.
- `precipitacion_diaria_mm` permanece completamente en `NaN`.
- `precipitacion_observada_mm` conserva la suma disponible para auditoria.
- Todas las filas tienen calidad `PENDIENTE_REGLA_COBERTURA`.
- Una particion completa puede identificarse y reanudarse por manifiesto.
- La reduccion de filas supera 99,4 % en las cuatro particiones.

## Ejecucion de `04_ClimateDailyAudit.ipynb`

La auditoria diaria se ejecuto con el commit `8b63e88` y termino en 1,79
segundos. El manifiesto quedo en estado `COMPLETA`.

- 2.987 filas diarias de entrada.
- 5.316 filas en el calendario estacion-sensor.
- 2.329 ausencias estacion-sensor; no todas representan un hueco departamental.
- 63 filas candidatas para revision.
- 21 coberturas mayores a 100 %, todas inferiores a 101,40 %.
- Dos pares de sensores paralelos y 76 comparaciones diarias.

El calendario distingue correctamente dos niveles: febrero tiene 21 dias sin
ningun registro en ambos departamentos, mientras otras ausencias corresponden a
estaciones individuales que no reportaron durante parte del mes.

Con una ventana candidata de cobertura entre 90 % y 102 %, 2.594 de 2.987 dias
observados, equivalentes al 86,84 %, pasan la prueba de completitud. Los 393 dias
con cobertura menor a 90 % permanecen parciales. El limite superior es una
tolerancia preliminar para la cadencia modal, no una validacion de observaciones
adicionales.

En sensores paralelos:

- Cundinamarca coincide dentro de 0,1 mm en los 38 dias compartidos.
- Boyaca coincide dentro de 0,1 mm en 31 de 38 dias.
- Boyaca presenta siete discrepancias; la maxima es 13,9 mm y en cinco dias un
  sensor reporta cero mientras el otro reporta lluvia.

## Decision y siguiente compuerta

El motor de deduplicacion, agregacion y trazabilidad queda validado para estos
pilotos. Aun no se aprueba ejecutar todo el historico ni llenar
`precipitacion_diaria_mm`.

La auditoria 04 queda validada. El contrato preliminar para disenar el
notebook 05 es:

1. Conservar dias ausentes como `NaN`; nunca convertirlos en cero.
2. Evaluar como aceptable una cobertura entre 90 % y 102 %, conservando el valor
   exacto de cobertura y una bandera de calidad.
3. Poner en cuarentena sensores con patrones persistentes compatibles con fallo,
   incluyendo `0035215030`/`0240` en el periodo piloto.
4. Mantener extremos aislados y p99 como observaciones marcadas, no eliminadas.
5. No promediar ni sumar sensores paralelos.
6. Seleccionar un sensor solo cuando haya concordancia o exista un unico sensor
   con calidad suficiente; una discrepancia material debe producir `NaN` y una
   bandera revisable.

Estas reglas se implementaran primero sobre los cuatro pilotos. El historico no
se procesara hasta comprobar que el notebook 05 conserva trazabilidad y no
convierte ausencias o desacuerdos en lluvia valida.
