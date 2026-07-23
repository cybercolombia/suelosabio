# Auditoria climatica: precipitacion, Boyaca, 2025

## Identificacion

| Campo | Valor |
|---|---|
| Variable | Precipitacion |
| Fuente Socrata | `s54a-sgyg` |
| Departamento | Boyaca |
| Periodo | 2025, meses 1 a 12 |
| Modo | Muestra estratificada y conteo completo por estacion/sensor |

La auditoria se ejecuto con dos bloques aleatorios de dos archivos contiguos por
particion mensual. El conteo completo leyo estacion, sensor y fecha de todos los
archivos seleccionados. Las demas metricas de calidad corresponden a la muestra.

## Alcance exacto

- 2.316 archivos Parquet.
- 2.311.516 filas segun metadatos Parquet.
- 28,27 MB.
- 12 particiones mensuales.
- Sin partes faltantes ni archivos ilegibles.
- Las 13 columnas esperadas aparecen en todos los archivos.

| Mes | Archivos | Filas | Tamano MB |
|---:|---:|---:|---:|
| 1 | 357 | 356.908 | 4,09 |
| 2 | 35 | 34.862 | 0,42 |
| 3 | 137 | 136.764 | 1,70 |
| 4 | 155 | 154.842 | 1,92 |
| 5 | 155 | 154.033 | 1,89 |
| 6 | 192 | 191.682 | 2,36 |
| 7 | 221 | 220.857 | 2,75 |
| 8 | 197 | 196.631 | 2,44 |
| 9 | 188 | 187.424 | 2,32 |
| 10 | 216 | 215.665 | 2,65 |
| 11 | 221 | 220.369 | 2,73 |
| 12 | 242 | 241.479 | 3,00 |

Enero contiene mas de diez veces las filas de febrero. El mismo patron aparece
en Cundinamarca y los conteos mensuales de ambos departamentos tienen una
correlacion de 0,988. Esto apunta a un comportamiento sistemico de la fuente,
no a una particularidad territorial, pero no demuestra por si solo su causa.

## Esquema y calidad muestral

Se encontraron dos firmas de esquema. La unica diferencia es el tipo de
`valorobservado`:

- `double` en 2.299 archivos y 2.296.394 filas.
- `int64` en 17 archivos y 15.122 filas.

La muestra contiene 48.000 filas tomadas de 48 archivos distintos:

- Sin nulos en las 13 columnas.
- Sin conversiones fallidas de fecha, valor, latitud o longitud.
- Sin coordenadas fuera de rango.
- Sin diferencias entre departamento del dato y particion.
- Unidad unica: `mm`.
- Valor minimo y mediana: 0 mm.
- Media: 0,0868 mm.
- Percentil 99: 0,4 mm.
- Maximo: 26,4 mm.

La media muestral no debe compararse como lluvia departamental con la de
Cundinamarca: la seleccion contiene fragmentos de dias, estaciones y cadencias
distintas.

## Duplicados

- 8.000 filas pertenecen a duplicados exactos.
- Representan el 16,67 % de la muestra.
- Forman 4.000 grupos duplicados.
- Eliminar una copia por grupo retiraria 4.000 filas, el 8,33 % de la muestra.
- No se observaron claves repetidas con valores distintos.
- Los 25 grupos conservados como ejemplo estan dentro de un mismo Parquet.

Esta proporcion no se extrapola al total. La duplicacion debe medirse sobre cada
particion completa durante el procesamiento diario.

## Estaciones, sensores y frecuencia

El conteo completo encontro 66 estaciones y 68 pares estacion-sensor:

| Sensor | Pares | Filas crudas | Cadencias detectadas |
|---|---:|---:|---|
| `0240` | 66 | 2.048.035 | 57 a 10 minutos, 8 a una hora, 1 sin inferir |
| `0257` | 2 | 263.481 | 1 a 2 minutos, 1 sin inferir |

Dos estaciones contienen mas de un sensor:

- `0024035340`: `0240` y `0257` durante casi todo el ano.
- `2403000117`: `0240` parcial y solo 24 filas de `0257` en una hora.

No se deben sumar sensores coexistentes. El procesamiento debe producir primero
una fila diaria por estacion y sensor; una etapa posterior escogera o consolidara
el sensor canonico con una regla de cobertura y calidad.

Dos pares no permitieron inferir frecuencia a partir de los bloques muestreados:

- `0023115010/0240`, con 542 filas entre enero y mayo.
- `2403000117/0257`, con 24 filas el 17 de octubre.

## Cobertura temporal preliminar

La cobertura teorica bruta compara las filas del conteo completo con la cantidad
esperada segun la cadencia modal. Se calcula antes de deduplicar y puede estar
inflada.

- Mediana: 75,67 %.
- 39 de 66 pares estan por debajo de 90 %.
- 16 de 66 pares estan por debajo de 50 %.
- 9 de 66 pares estan por debajo de 25 %.
- 45 de 66 pares con frecuencia inferida abarcan al menos 360 dias.

La existencia de carpetas para los 12 meses no significa que cada estacion tenga
los 365 dias. La cobertura diaria real se calculara despues de deduplicar.

## Geografia

La muestra contiene 65 estaciones con etiqueta geografica. No se observaron
cambios de nombre, departamento, municipio ni coordenadas redondeadas dentro de
esta muestra. Esto contrasta con Cundinamarca, donde 19 estaciones fueron
marcadas por geografia variable.

El resultado no reemplaza la tabla canonica de estaciones ni el cruce posterior
con DIVIPOLA.

## Comparacion con Cundinamarca

| Metrica | Boyaca | Cundinamarca |
|---|---:|---:|
| Filas exactas | 2.311.516 | 2.304.482 |
| Estaciones | 66 | 55 |
| Pares estacion-sensor | 68 | 56 |
| Cobertura teorica bruta mediana | 75,67 % | 84,70 % |
| Pares bajo 50 % de cobertura | 16 | 11 |
| Pares con alcance de al menos 360 dias | 45 | 39 |
| Duplicados exactos en muestra | 16,67 % | 16,97 % |
| Estaciones con alerta geografica muestral | 0 | 19 |

Los dos territorios comparten esquema, unidad, codigos de sensor, duplicacion,
sensores paralelos y cadencias heterogeneas. Por ello pueden usar el mismo motor
de procesamiento, con diagnosticos y decisiones conservadas por particion.

## Decisiones para el siguiente paso

1. Conservar los Parquet crudos sin cambios.
2. Homologar `valorobservado` a decimal durante la lectura.
3. Deduplicar filas exactas antes de agregar.
4. Reportar duplicados y conflictos por mes, estacion y sensor.
5. Producir una fila diaria por estacion-sensor, sin sumar sensores paralelos.
6. Calcular cobertura diaria exacta y conservar dias incompletos con banderas.
7. No imputar lluvia ni eliminar extremos en esta primera transformacion.
8. Confirmar la semantica incremental con muestras historicas antes de cerrar la
   suma diaria como regla definitiva.

## Fuente

- [Precipitacion - Datos Abiertos Colombia](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Precipitaci-n/s54a-sgyg)
