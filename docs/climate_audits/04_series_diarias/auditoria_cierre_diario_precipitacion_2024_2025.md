# Auditoria de cierre diario de precipitacion 2024-2025

**Fecha de ejecucion:** 23 de julio de 2026  
**Fuente:** `s54a-sgyg`  
**Alcance:** Boyaca y Cundinamarca, enero de 2024 a diciembre de 2025  
**Auditor:** `auditoria_precipitacion_diaria_v2`  
**Commit:** `2b44159`  
**Estado de ejecucion:** `COMPLETA`  
**Estado de aprobacion:** pendiente de resolver una estacion atipica antes de 05

## Resultado general

La auditoria leyo las 48 particiones `COMPLETA` producidas por el paso 03 y
termino en 18,43 segundos. No modifico ni imputo observaciones.

| Metrica | Resultado |
|---|---:|
| Filas estacion-sensor-dia observadas | 42.190 |
| Filas del calendario | 55.290 |
| Dias estacion-sensor ausentes, conservados como `NaN` | 13.100 |
| Pares estacion-sensor en el catalogo | 130 |
| Ausencias de mes completo dentro del intervalo activo | 102 |
| Filas candidatas para revision | 464 |
| Pares de sensores paralelos | 4 |

El catalogo considera esperado cada par estacion-sensor solamente entre su
primer y ultimo mes observado. Por tanto, las 102 ausencias son huecos internos;
no suponen que una estacion debio existir antes de su alta o despues de su baja.

## Cobertura por departamento y ano

| Departamento | Ano | Observadas | Calendario | Ausentes | Pares-mes ausentes | Dias sin registros en todo el departamento | Cobertura baja | Cobertura mayor a 100 % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Boyaca | 2024 | 7.284 | 9.954 | 2.670 | 16 | 10 | 1.010 | 23 |
| Boyaca | 2025 | 16.073 | 21.181 | 5.108 | 59 | 29 | 1.383 | 40 |
| Cundinamarca | 2024 | 4.794 | 6.927 | 2.133 | 9 | 14 | 932 | 12 |
| Cundinamarca | 2025 | 14.039 | 17.228 | 3.189 | 18 | 29 | 951 | 7 |

Entre las 42.190 filas observadas:

- 37.831 tienen cobertura entre 90 % y 100 %.
- 79 tienen cobertura mayor a 100 % y menor o igual a 102 %.
- 3 superan 102 %; el maximo es 312,5 %.
- 4.276 tienen cobertura inferior a 90 %.
- 1 fila no tiene cobertura evaluable.

El paso 05 solo considera candidato un sensor con cobertura entre 90 % y 102 %.
Las coberturas fuera de ese intervalo permanecen sin valor consolidado.

## Hallazgos de continuidad

- Febrero de 2025 conserva la interrupcion transversal ya identificada: ambos
  departamentos solo tienen algun registro en 7 de 28 dias.
- Boyaca tiene 1.319 filas estacion-sensor ausentes en febrero de 2025 y
  Cundinamarca tiene 1.000.
- El par `0035027190/0240` de Cundinamarca solo aparece en 2 de los 13 meses
  comprendidos entre su primera y ultima observacion.
- El par `0024035370/0240` de Boyaca aparece en 4 de 16 meses esperados.
- Ninguna ausencia fue convertida en cero ni interpolada.

## Valores y sensores en revision

Los motivos no son excluyentes:

| Motivo | Filas |
|---|---:|
| `COBERTURA_MAYOR_100` | 82 |
| `EXTREMO_P99_PARTICION` | 249 |
| `INTERVALO_MUY_ALTO` | 223 |
| `POSITIVOS_PERSISTENTES` | 171 |
| `TOTAL_DIARIO_MUY_ALTO` | 199 |

### Cuarentena ya cubierta por el contrato

`0035215030/0240`, Boyaca, acumula 170 dias con el patron
`POSITIVOS_PERSISTENTES`, entre noviembre de 2024 y septiembre de 2025. Su
mediana entre filas revisadas es 518,4 mm/dia y alcanza 4.236,3 mm/dia.

La regla vigente de 05 pone en cuarentena un sensor con tres o mas dias de ese
patron. Una simulacion de solo lectura sobre el cierre confirmo que este sensor
queda completamente excluido como candidato.

### Compuerta pendiente: `3505500121/0240`

La estacion `PIDEMONTE CHINGAZA`, municipio de Medina, presenta un segundo
patron que la regla vigente no pone en cuarentena:

- 23 dias superan 200 mm y 60 dias quedan en revision.
- El maximo es 616 mm/dia.
- Junio de 2025 suma 3.272 mm y tiene mediana de 88,5 mm/dia.
- En agosto de 2025 el total cae abruptamente a 49,6 mm.
- En sus 15 dias mas altos, el maximo de las demas estaciones de Cundinamarca
  queda entre 17,7 y 103 mm, mientras esta estacion registra entre 273 y 616 mm.

Esto es compatible con un problema instrumental o semantico recurrente, no con
un extremo aislado. La evidencia disponible no basta para declarar cada valor
invalido, pero tampoco respalda incorporarlos automaticamente al agregado.

**Decision pendiente antes de 05:** contrastar con crudos o una estacion vecina
y aprobar una cuarentena explicita. Mientras tanto, no ejecutar la consolidacion
definitiva 2024-2025.

## Sensores paralelos

Se encontraron cuatro pares. La regla de consolidacion sigue siendo adecuada:

- No se suman ni se promedian sensores paralelos.
- Si dos sensores validos discrepan mas de 0,1 mm, el dia queda en `NaN`.
- `3502500135` tiene 683 dias compartidos; 680 concuerdan y 3 requieren la
  proteccion por discrepancia.

## Simulacion del paso 05

Se ejecuto localmente el contrato `precipitacion_estacion_dia_v1` en memoria,
sin escribir productos:

| Metrica | Resultado |
|---|---:|
| Filas estacion-dia | 53.128 |
| Dias aceptados | 36.187 |
| Dias sin observacion | 12.595 |
| Dias observados sin sensor valido | 4.214 |
| Dias con sensores discrepantes | 132 |
| Sensores en cuarentena | 1 |

La simulacion confirma la trazabilidad y las protecciones conocidas, pero
tambien que `3505500121/0240` seria aceptado actualmente. Por ello el paso 04 no
se considera aprobado para escalar hasta cerrar esa decision.

## Conclusion

La ejecucion tecnica de 04 esta completa y cubre continuidad, cobertura,
extremos y sensores paralelos. La unica compuerta nueva para 05 es el tratamiento
de `3505500121/0240`. Febrero de 2025 y las demas ausencias deben permanecer
como `NaN`; no son motivo para detener el pipeline.
