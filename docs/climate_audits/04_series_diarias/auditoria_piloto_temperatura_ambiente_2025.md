# Auditoria piloto diaria de temperatura ambiente

**Fecha de revision:** 25 de julio de 2026  
**Fuente:** `sbwg-7ju4`  
**Alcance:** Boyaca y Cundinamarca, enero-febrero de 2025  
**Estado:** requiere repetir 03 y 04 con los contratos v2 antes de escalar

La corrida v1 termino `COMPLETA` para las cuatro particiones y permite validar
la trazabilidad general. Tambien revelo un error en la inferencia de cadencia:
los saltos entre dias aislados se estaban interpretando como frecuencia de
muestreo. Por eso este reporte conserva la evidencia v1, pero no aprueba la
escala 2024-2025.

## Procedencia

| Departamento | Mes | Filas estacion-sensor-dia | Pares estacion-sensor |
|---|---:|---:|---:|
| Boyaca | 1 | 759 | 28 |
| Boyaca | 2 | 109 | 27 |
| Cundinamarca | 1 | 851 | 30 |
| Cundinamarca | 2 | 129 | 29 |

El conjunto contiene 1.848 filas observadas. El calendario expandido contiene
3.366 filas y 1.518 ausencias estacion-sensor-dia.

## Hueco transversal de febrero

Enero tiene al menos un registro en sus 31 dias para ambos departamentos.
Febrero solo tiene observaciones los dias 1 al 4 y 26 al 28: faltan por completo
los dias 5 al 25 en Boyaca y Cundinamarca.

El patron coincide con el hallazgo transversal de precipitacion. No es un error
del calendario ni una orden para interpolar. Los 21 dias deben permanecer como
ausencias explicitas (`NaN`) y con procedencia trazable.

## Error detectado en cobertura v1

La estacion `0035215030`, sensor `0068`, tiene observaciones aisladas. La
version v1 calculo intervalos modales de 61.200 y 226.800 segundos usando saltos
entre dias distintos. Eso produjo coberturas imposibles de 141,67 % y 262,50 %.

La causa esta en el contrato de 03, no en los valores diarios de temperatura.
El contrato v2 corrige el calculo:

1. Inferir intervalos por estacion-sensor-dia, solo entre observaciones del
   mismo dia.
2. Evaluar cobertura solo para cadencias reconocidas de 1, 2, 10 o 60 minutos.
3. Conservar cadencias escasas o desconocidas como `NO_EVALUABLE`, con
   observaciones esperadas y cobertura en `NaN`.
4. Usar 102 % como tolerancia superior diagnostica; valores entre 100 y 102 %
   no son una alerta automatica.

## Amplitud y extremos

No aparecieron temperaturas por debajo de -10 grados C ni por encima de
45 grados C. Diez filas superaron la amplitud diagnostica de 25 grados C,
principalmente en la estacion `0024035340`, sensores `0068` y `0071`.

Esas filas se conservan para revision. Una amplitud alta no demuestra por si
sola un fallo instrumental y no autoriza eliminacion ni imputacion.

## Sensores paralelos

Se encontraron dos estaciones con sensores `0068` y `0071` en paralelo:

| Departamento | Estacion | Dias compartidos | Dias dentro de 1 grado C | Diferencia maxima v1 |
|---|---|---:|---:|---:|
| Boyaca | `0024035340` | 38 | 36 | 1,68 grados C |
| Cundinamarca | `3502500135` | 38 | 37 | 3,22 grados C |

Las tres discrepancias superiores a 1 grado C ocurrieron cuando al menos uno de
los sensores tenia cobertura inferior a 90 %. La auditoria v2 solo calificara
concordancia si ambos sensores tienen cobertura evaluable entre 90 y 102 %.
Los sensores siguen separados; este paso no los promedia ni selecciona.

## Decision

- El motor diario y las llaves estacion-sensor-dia quedan validados de forma
  preliminar.
- La version v1 de cobertura no es defendible y se reemplaza por
  `temperatura_diaria_v2`.
- La auditoria se reemplaza por `auditoria_temperatura_diaria_v2`.
- Se deben sobrescribir solamente las cuatro particiones piloto con 03 v2 y
  repetir 04.
- No se ejecutan aun las 48 particiones de 2024-2025.
- No se imputa ningun dia y no se ejecuta 05 hasta aprobar el piloto v2.
