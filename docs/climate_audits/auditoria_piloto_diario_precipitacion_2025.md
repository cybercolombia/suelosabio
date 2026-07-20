# Auditoria piloto del procesamiento diario de precipitacion

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

## Validaciones superadas

- Las cuatro llaves `estacion + sensor + fecha` son unicas en la salida diaria.
- Los sensores paralelos permanecen separados.
- `precipitacion_diaria_mm` permanece completamente en `NaN`.
- `precipitacion_observada_mm` conserva la suma disponible para auditoria.
- Todas las filas tienen calidad `PENDIENTE_REGLA_COBERTURA`.
- Una particion completa puede identificarse y reanudarse por manifiesto.
- La reduccion de filas supera 99,4 % en las cuatro particiones.

## Decision y siguiente compuerta

El motor de deduplicacion, agregacion y trazabilidad queda validado para estos
pilotos. Aun no se aprueba ejecutar todo el historico ni llenar
`precipitacion_diaria_mm`.

El siguiente notebook, `03_01_ClimateDailyAudit.ipynb`, debe resolver:

1. Construccion del calendario y reporte de dias completamente ausentes.
2. Umbral de cobertura para aceptar un dia.
3. Coberturas superiores a 100 % y cambios de cadencia.
4. Deteccion de valores constantes, saturacion y extremos sospechosos.
5. Concordancia y seleccion posterior de sensores paralelos.
