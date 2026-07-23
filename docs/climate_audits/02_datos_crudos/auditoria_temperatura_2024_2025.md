# Sintesis de auditoria cruda de temperatura

**Fuentes:** `sbwg-7ju4`, `afdg-3zpb`, `ccvq-rp9s`  
**Departamentos:** Boyaca y Cundinamarca  
**Evidencia recibida:** auditorias muestrales del notebook 02  
**Estado:** suficiente para un piloto diario; insuficiente para declarar cobertura
historica completa

## Cobertura realmente comprobada

| Variable | Dataset | Sensor(es) | Periodo comprobado por inventario |
|---|---|---|---|
| Temperatura ambiente | `sbwg-7ju4` | `0068`, `0071` | 2024-2025, ambos departamentos |
| Temperatura minima | `afdg-3zpb` | `0070` | 2025, ambos departamentos |
| Temperatura maxima | `ccvq-rp9s` | `0069` | 2025, ambos departamentos |

Las carpetas de auditoria de minima y maxima fueron etiquetadas como
`2025_2026`, pero sus inventarios contienen exclusivamente 2025. El equipo
reporta haber descargado tambien 2024; esa existencia debe verificarse en
`clima_crudo` y no se considera auditada todavia.

## Hallazgos comunes

- Las tres fuentes conservan las 13 columnas del contrato climatico y usan
  grados Celsius (`°C`).
- No hubo fallos de conversion numerica o temporal en las muestras.
- Existen duplicados exactos abundantes. Debe conservarse una observacion por
  `estacion + sensor + timestamp` y exportar los descartes.
- Los conflictos con valores distintos para la misma clave no deben
  promediarse. Se excluyen del agregado y se conservan en `conflictos.parquet`.
- Las cadencias cambian por estacion y sensor. La cobertura diaria debe
  calcularse con la cadencia del par, no con el numero bruto de filas.
- La actividad de febrero de 2025 cae de forma marcada en ambos departamentos
  y en las tres fuentes. Se trata como posible hueco sistemico hasta demostrar
  lo contrario; no se rellena con cero ni se imputa en 03.
- Varias estaciones presentan coordenadas variables. La geografia canonica se
  resolvera en una etapa posterior y no sobrescribiendo el crudo.

La evidencia transversal y la diferencia entre caida de volumen y hueco diario
confirmado se detallan en
[`../transversales/alerta_cobertura_febrero_2025.md`](../transversales/alerta_cobertura_febrero_2025.md).

## Evidencia por fuente

### Temperatura ambiente

- Descripciones: `TEMPERATURA DEL AIRE A 2 m` y
  `GPRS - TEMPERATURA DEL AIRE A 2 m`.
- Cadencias modales observadas: 120, 600 y 3600 segundos; aparecio un caso
  muestral de 10800 segundos para revision.
- Muestra 2025: 96.000 filas; rango de 0,0 a 35,9 °C; 12.594 filas dentro de
  grupos duplicados exactos y cero conflictos.
- El sensor GPRS de dos minutos no se mezcla ni pondera junto con el sensor
  convencional. Ambos permanecen separados durante 03.

### Temperatura minima

- Descripcion: `TEMPERATURA MÍNIMA DEL AIRE A 2 m`.
- Cadencia principal: 3600 segundos; aparecieron pares con modas de 60 y 2580
  segundos para revision.
- Muestra 2025: 92.301 filas; rango de -5,1 a 43,7 °C; 12.184 filas dentro de
  grupos duplicados exactos y cero conflictos.

### Temperatura maxima

- Descripcion: `TEMPERATURA DEL AIRE MÁXIMA A 2 m`.
- Cadencia principal: 3600 segundos; aparecio un par irregular con moda de
  18000 segundos.
- Muestra 2025: 91.791 filas; rango de 0,0 a 49,8 °C; 12.440 filas dentro de
  grupos duplicados exactos.
- Se detecto un conflicto real en la muestra: estacion `3502500135`, sensor
  `0069`, `2025-01-09 23:01:00`, con 19,3 y 20,9 °C. Debe quedar excluido y
  trazable, no promediado.

## Contrato diario aprobado para piloto

El modulo `TemperatureRules.py` implementa `temperatura_diaria_v1`:

- Ambiente conserva media, mediana, minimo, maximo, desviacion y amplitud; su
  estadistico principal preliminar es la media.
- Minima conserva los mismos descriptores; su estadistico principal es el
  minimo diario observado.
- Maxima conserva los mismos descriptores; su estadistico principal es el
  maximo diario observado.
- Ninguna temperatura se suma.
- El rango operativo de entrada `[-30, 60] °C` solo captura codigos o valores
  fisicamente incompatibles muy evidentes. Los umbrales diagnosticos mas
  estrechos de 04 marcan candidatos, pero no eliminan observaciones.
- `temperatura_diaria_c` permanece en `NaN` hasta aprobar cobertura y seleccion
  de sensor despues de 04.

## Intento fallido anterior

Cinco particiones de temperatura ambiente 2025 quedaron con manifiesto
`INICIADA` y archivos `manifest_error_*`, sin ningun Parquet diario. Los
manifiestos registran `precipitacion_incremental_v1`: el procesador de
precipitacion rechazo todas las filas de temperatura y luego informo que la
particion no produjo observaciones diarias.

Estas carpetas no contienen resultados recuperables. Antes del nuevo piloto se
deben eliminar o apartar unicamente esas salidas incompletas de
`clima_diario_sensor/variable=temperatura_ambiente`; nunca se elimina
`clima_crudo`. Alternativamente puede usarse sobrescritura de forma controlada,
pero los manifiestos de error anteriores permanecerian como evidencia historica.

## Siguiente compuerta

1. Ejecutar 03 para una particion de ambiente de enero y otra de febrero de
   2025 por departamento.
2. Confirmar manifiestos `COMPLETA`, estadisticos diarios, rechazos, conflictos
   y cobertura.
3. Ejecutar 04 sobre esos cuatro pilotos.
4. Revisar diferencias entre `0068` y `0071`, extremos, amplitud y el hueco de
   febrero.
5. Solo entonces definir el contrato de consolidacion de temperatura para 04.
