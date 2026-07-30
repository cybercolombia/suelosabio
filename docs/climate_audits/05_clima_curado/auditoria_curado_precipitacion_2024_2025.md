# Auditoria del curado diario de precipitacion 2024-2025

**Fecha de ejecucion:** 23 de julio de 2026
**Fuente:** `s54a-sgyg`
**Alcance:** Boyaca y Cundinamarca, enero de 2024 a diciembre de 2025
**Contrato:** `precipitacion_estacion_dia_v2`
**Commit:** `ccd0573e9c4ab12620c8d3787eb4a69b12219ebc`
**Estado:** `COMPLETA` y reconciliada

## Ejecucion

`05_Climate_Precipitation_DailyConsolidator.ipynb` consumio la auditoria
`cierre_precipitacion_2024_2025_v1`, version
`auditoria_precipitacion_diaria_v2`. La corrida en Colab duro 380,64 segundos
y genero 48 particiones mensuales.

| Metrica | Resultado |
|---|---:|
| Filas del calendario de entrada | 55.290 |
| Filas estacion-dia de salida | 53.128 |
| Dias con precipitacion aceptada | 36.288 |
| Dias sin observacion | 12.595 |
| Dias observados sin sensor valido | 4.113 |
| Dias con sensores discrepantes | 132 |
| Filas sensor-dia ajustadas | 228 |
| Filas estacion-dia seleccionadas con ajuste | 219 |
| Sensores con ventana de cuarentena | 1 |

## Reconciliacion independiente

La revision local leyo directamente los 48 Parquet de salida y comprobo:

- Las 53.128 filas reales coinciden con el manifiesto y el resumen de calidad.
- No existen llaves duplicadas para `departamento + estacion + fecha`.
- Cada archivo contiene unicamente el departamento, ano y mes indicados por su
  ruta.
- El intervalo cubre del 1 de enero de 2024 al 31 de diciembre de 2025.
- `SIN_OBSERVACION`, `SIN_SENSOR_VALIDO` y `SENSORES_DISCREPANTES` conservan
  `precipitacion_diaria_mm=NaN`.
- Todo valor no nulo tiene una calidad que comienza por `VALIDO`.

## Ajuste y cuarentena

La calibracion `medina_3505500121_decimas_mm_v1` se aplico exclusivamente a
`3505500121/0240`, Cundinamarca, entre el 29 de octubre de 2024 y el 21 de julio
de 2025. Las 228 filas sensor-dia cumplen
`valor_ajustado = valor_original * 0,1`; 219 fueron seleccionadas como valor
estacion-dia. Valor original, ajustado, factor, motivo y evidencia permanecen
en la salida.

`0035215030/0240`, Boyaca, queda en cuarentena solo entre el 1 de noviembre de
2024 y el 16 de septiembre de 2025. Se verificaron 101 dias candidatos validos
fuera de esa ventana, por lo que la regla no elimina la historia confiable del
sensor.

## Distribucion de calidad

| Calidad | Filas |
|---|---:|
| `VALIDO_SENSOR_UNICO` | 34.830 |
| `VALIDO_SENSORES_CONCORDANTES` | 1.239 |
| `VALIDO_AJUSTADO_SENSOR_UNICO` | 219 |
| `SIN_OBSERVACION` | 12.595 |
| `SIN_SENSOR_VALIDO` | 4.113 |
| `SENSORES_DISCREPANTES` | 132 |

El maximo aceptado es 385,7 mm. Corresponde al extremo aislado
`0035160020/0240`, Boyaca, del 12 de mayo de 2024 y conserva banderas de
revision; no pertenece al cambio de escala corregido.

## Conclusion

El paso 05 queda aprobado para precipitacion 2024-2025. La capa puede alimentar
el paso 06, pero aun no debe interpretarse como serie municipal ni como serie
imputada. Las ausencias y descartes permanecen explicitos.
