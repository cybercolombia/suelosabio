# Ciclo climático por variable

**Actualizado:** 30 de julio de 2026
**Ventana de estaciones:** 2024–2025
**Territorio:** 123 municipios de Boyacá y 116 de Cundinamarca

## Propósito y fases comunes

El pipeline histórico convierte observaciones IDEAM de frecuencia irregular en
una capa municipio-día auditable:

```text
01 descarga inmutable
  → 02 auditoría cruda y contrato
  → 03 estación × sensor × día
  → 04 auditoría diaria
  → 05 estación × día curada
  → 06 asignación geográfica canónica
  → 07 municipio × día
  → 08 indicadores por período agrícola
```

Los pasos 03–07 existen para seis variables. Humedad permanece bloqueada antes
de 03: tener archivos crudos no autoriza inventar su contrato.

## Tablero verificado

| Variable | Fuente | 01–02 | 03–05 | 06 | 07 | 08 |
|---|---|---|---|---|---|---|
| Precipitación | `s54a-sgyg` | Completo con alertas | Completo | Canónica v3 | Producto completo; revisión científica pendiente | Pendiente para estaciones |
| Temperatura ambiente | `sbwg-7ju4` | Completo | Completo | Completo | Completo | Pendiente para estaciones |
| Temperatura mínima | `afdg-3zpb` | Completo | Completo | Completo | Completo | Pendiente para estaciones |
| Temperatura máxima | `ccvq-rp9s` | Completo | Completo | Completo | Completo | Pendiente para estaciones |
| Velocidad del viento | `sgfv-3yp8` | Completo | Completo | Completo | Completo | Pendiente para estaciones |
| Presión atmosférica | `62tk-nxj5` | Completo | Completo | Completo | Completo | Pendiente para estaciones |
| Humedad | `uext-mhny` | Parcial | Bloqueado | Bloqueado | Bloqueado | Bloqueado |

El paso 08 sí fue construido para el dataset de pronóstico usando NASA POWER.
Esa fuente es una malla diaria completa y se documenta por separado en
[Pronóstico](forecast.md). No debe confundirse con la red de estaciones.

## Controles comunes de descarga y auditoría

Cada fuente se particiona por variable, departamento, año y mes. La auditoría
verifica:

- esquema, tipos, unidad y pertenencia a la partición;
- fechas internas y cadencia observada;
- códigos de estación y sensor;
- duplicados exactos y claves con valores contradictorios;
- valores fuera del rango operativo;
- cambios de coordenadas o etiquetas;
- continuidad y meses ausentes.

El problema transversal más importante fue la ausencia de observaciones entre
el 5 y el 25 de febrero de 2025. No se imputó ni se interpretó como cero.

## Precipitación

| Aspecto | Contrato y resultado |
|---|---|
| Unidad | Milímetros |
| Sensores | Sensores cuya descripción corresponde a precipitación |
| Frecuencias observadas | 1, 2, 5, 10 y 60 minutos |
| Homogeneización diaria | Los valores son incrementos del intervalo y se suman por día |
| Conflictos | Se excluyen; no se promedian |
| Valores negativos | Se rechazan |
| Consolidación estación-día | Selección trazable entre sensores; conserva cobertura, diferencias, cuarentena y ajuste |
| Agregado municipal | Mediana no ponderada de estaciones válidas, con media, extremos, dispersión y cobertura como diagnósticos |

La auditoría diaria encontró 102 ausencias de mes completo dentro de intervalos
activos. El sensor `0035215030/0240` tuvo un patrón instrumental sospechoso y fue
puesto en cuarentena donde aplicaba. El sensor `3505500121/0240` cambió de escala;
se aplicó factor 0,1 entre el 29 de octubre de 2024 y el 21 de julio de 2025,
conservando valor original, ajustado, motivo y evidencia.

Resultados principales:

- 48 particiones mensuales procesadas;
- 42.190 filas estación-sensor-día;
- 53.128 filas estación-día reconciliadas;
- 116 estaciones asignadas canónicamente, 9 en revisión y 1 excluida;
- 174.709 filas municipio-día;
- 84 municipios con estación canónica utilizable y 155 sin ella;
- 68,67 % de cobertura temporal dentro del universo con estación esperada.

La capa municipal existe, pero Aquitania y Puerto Salgar requieren revisión de
sensibilidad media-mediana y aún debe aprobarse el umbral de cobertura para
indicadores de período.

## Temperatura ambiente

| Aspecto | Contrato y resultado |
|---|---|
| Fuente y sensores | `sbwg-7ju4`; sensores `0068` y `0071` |
| Unidad y rango | Grados Celsius; rango operativo −30 a 60 |
| Homogeneización diaria | Media diaria con cadencia inferida dentro de cada día |
| Auditoría cruda | 2.477 archivos, 2.452.584 filas inventariadas y muestra contigua de 190.969 |
| Auditoría diaria | 31.966 filas estación-sensor-día |
| Geografía | 35 asignaciones canónicas en Boyacá y 47 en Cundinamarca |
| Municipio-día | Calendario de 239 municipios; ausencias conservadas |

Los duplicados equivalentes se reducen con trazabilidad. Las claves con valores
distintos se excluyen. Doce estaciones conservaron alertas de movimiento
superior a 100 metros o variación de etiqueta. Los extremos, amplitudes y baja
cobertura se reportan, no se corrigen mediante imputación.

## Temperatura mínima

| Aspecto | Contrato y resultado |
|---|---|
| Fuente y sensor | `afdg-3zpb`; sensor `0070` |
| Unidad y rango | Grados Celsius; rango operativo −30 a 60 |
| Homogeneización diaria | Mínimo diario |
| Auditoría cruda | 747 archivos, 718.097 filas y muestra de 165.377 |
| Conflictos auditados | Sin claves crudas con valores contradictorios en el cierre |
| Auditoría diaria | 25.120 filas estación-sensor-día |
| Geografía | 34 asignaciones canónicas en Boyacá y 37 en Cundinamarca |
| Municipio-día | Calendario completo; la falta de red o lectura es ausencia |

## Temperatura máxima

| Aspecto | Contrato y resultado |
|---|---|
| Fuente y sensor | `ccvq-rp9s`; sensor `0069` |
| Unidad y rango | Grados Celsius; rango operativo −30 a 60 |
| Homogeneización diaria | Máximo diario |
| Auditoría cruda | 738 archivos, 713.806 filas y muestra de 161.473 |
| Conflictos auditados | Cuatro claves con valores contradictorios; se excluyeron |
| Auditoría diaria | 24.961 filas estación-sensor-día |
| Geografía | 34 asignaciones canónicas en Boyacá y 37 en Cundinamarca |
| Municipio-día | Calendario completo con cobertura y alertas |

## Velocidad del viento

| Aspecto | Contrato y resultado |
|---|---|
| Fuente y sensor | `sgfv-3yp8`; sensor `0103` |
| Unidad y rango | Metros por segundo; rango operativo 0 a 100 |
| Homogeneización diaria | Media diaria |
| Auditoría cruda | 4.901 archivos, 4.877.266 filas y muestra contigua de 191.193 |
| Auditoría diaria | 29.708 filas estación-sensor-día |
| Geografía | 33 asignaciones canónicas en Boyacá y 46 en Cundinamarca |
| Municipio-día | Calendario completo de 239 municipios |

Doce estaciones conservaron alertas de movimiento o variación de etiqueta. Los
extremos y amplitudes se mantienen como banderas; sensores discrepantes no se
promedian.

## Presión atmosférica

| Aspecto | Contrato y resultado |
|---|---|
| Fuente y sensor | `62tk-nxj5`; sensor `0255` |
| Unidad y rango | Hectopascales; rango operativo 400 a 1.100 |
| Homogeneización diaria | Media diaria |
| Auditoría cruda | 1.641 archivos, 1.620.915 filas y muestra contigua de 190.792 |
| Auditoría diaria | 27.782 filas estación-sensor-día |
| Geografía | 31 asignaciones canónicas en Boyacá y 42 en Cundinamarca |
| Municipio-día | Calendario completo de 239 municipios |

Once estaciones conservaron alertas por coordenadas o etiquetas. El valor diario
no se corrige por altura ni se imputa: esas transformaciones requerirían un
contrato científico adicional.

## Humedad

Solo hay evidencia cruda parcial. La ficha auditada de Cundinamarca 2025 no es
suficiente para fijar unidad, sensores, rango, estadístico diario y cobertura.
`HumidityRules.py` detiene deliberadamente la ejecución. Antes de habilitar 03
se requiere:

1. completar 02 para ambos departamentos y años;
2. contrastar la brecha de febrero de 2025;
3. aprobar unidad, sensores, rango y regla de duplicados;
4. probar un piloto de enero-febrero de 2025;
5. auditar el piloto antes de escalar.

## Productos y lectura correcta

- `clima_crudo`: observaciones descargadas, inmutables.
- `auditorias_climaticas`: inventario y hallazgos de la fuente cruda.
- `clima_diario_sensor`: una fila por estación, sensor y día.
- `auditorias_clima_diario`: cobertura, continuidad, extremos y conflictos.
- `clima_diario_curado`: una fila por estación y día.
- `geografia_curada`: catálogo y asignación canónica a municipio.
- `clima_municipal`: una fila por municipio y día.

Los detalles de ejecución y los manifiestos están indexados en
[`../data_artifacts.md`](../data_artifacts.md). Los reportes de evidencia se
conservan en `docs/climate_audits/`.
