# Auditoria climatica de precipitacion, 2024

**Actualizado:** 22 de julio de 2026  
**Estado:** evidencia aprobada para escalar el paso 03  
**Fuente:** `s54a-sgyg`  
**Alcance:** Boyaca y Cundinamarca, enero-diciembre de 2024

Esta sintesis compara las dos auditorias muestrales de cierre producidas por
`02_ClimateDataAudit.ipynb`. El inventario de archivos, filas y esquemas es
completo. Nulos, conversiones, valores, duplicados, conflictos, cadencias y
geografia se evaluaron sobre una muestra estratificada de 48.000 filas por
departamento.

## Alcance verificado

| Departamento | Particiones | Archivos | Filas exactas | Tamano | Filas muestra |
|---|---:|---:|---:|---:|---:|
| Boyaca | 12 | 1.724 | 1.716.496 | 19,53 MB | 48.000 |
| Cundinamarca | 12 | 1.872 | 1.866.195 | 21,84 MB | 48.000 |
| **Total** | **24** | **3.596** | **3.582.691** | **41,37 MB** | **96.000** |

Las 24 particiones comienzan en `part-00000`, no tienen partes intermedias
faltantes ni errores de lectura. Los ultimos archivos contienen menos de 1.000
filas, de acuerdo con la paginacion de la descarga.

## Esquema y calidad

- Las 13 columnas esperadas aparecen en los 3.596 archivos.
- `fechaobservacion` es `timestamp[ns]`; las columnas de identificacion son
  texto y las coordenadas son decimales.
- La unica variante de esquema es `valorobservado` como `double` o `int64`.
  El paso 03 ya lo convierte a numerico antes de procesar.
- La muestra no contiene nulos ni conversiones fallidas.
- Las 96.000 fechas coinciden con su ano y mes de particion.
- La unidad observada es exclusivamente `mm`.
- No se observaron coordenadas fuera de rango ni alertas geograficas en la
  muestra.

## Valores, duplicados y conflictos

| Metrica muestral | Boyaca | Cundinamarca |
|---|---:|---:|
| Minimo | 0 mm | 0 mm |
| Mediana | 0 mm | 0 mm |
| Percentil 99 | 1,0 mm | 0,2 mm |
| Maximo | 25,6 mm | 28,0 mm |
| Filas dentro de grupos duplicados exactos | 12.000 | 9.996 |
| Grupos duplicados exactos | 6.000 | 4.998 |
| Claves con valores conflictivos | 0 | 0 |

La ausencia de conflictos es muestral. El paso 03 revisa todas las filas de
cada particion y exporta cualquier conflicto encontrado. La duplicacion
observada es abundante, pero coincide con el problema ya cubierto por
`PrecipitationRules.py`.

## Cadencias y sensores

| Departamento | Sensor | Cadencias modales observadas |
|---|---|---|
| Boyaca | `0240` | 10 y 60 minutos |
| Boyaca | `0257` | 2 minutos |
| Cundinamarca | `0240` | 1, 10 y 60 minutos |
| Cundinamarca | `0257` | 1 minuto |

Todas pertenecen al conjunto de cadencias admitidas por el contrato vigente:
1, 2, 5, 10 y 60 minutos. Los sensores paralelos permanecen separados en el
paso 03.

La densidad aumenta con fuerza al final de 2024. En Boyaca los archivos pasan de
113 en septiembre a 375 en noviembre; en Cundinamarca pasan de 122 a 412. La
muestra tambien detecta mas estaciones activas desde septiembre-octubre. Esto
parece una ampliacion o reactivacion de la red y no un error de particionado.
Debe quedar visible en la auditoria diaria y en el futuro catalogo esperado de
estaciones.

## Decision

La evidencia de 2024 es compatible con el contrato
`precipitacion_incremental_v1`. No se modifica `PrecipitationRules.py` antes de
escalar.

Se aprueba ejecutar el paso 03 para las 44 particiones pendientes del objetivo
2024-2025. La aprobacion no convierte toda observacion en valida: el paso 03
debe conservar sus balances, rechazos, duplicados y conflictos por particion, y
el paso 04 debe evaluar calendario, cobertura y sensores antes del paso 05.
