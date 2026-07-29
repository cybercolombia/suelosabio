# Agregacion municipal diaria de precipitacion

**Actualizado:** 29 de julio de 2026
**Estado:** corrida oficial completa y validada; revision cientifica de cobertura pendiente
**Alcance:** Boyaca y Cundinamarca, 2024-2025

`07_ClimateMunicipalAggregator.ipynb` transforma la capa de precipitacion
estacion-dia en un calendario municipio-dia auditable. No modifica los
artefactos de los pasos 05 y 06.

## Entradas

```text
eco2026_processed/
  clima_diario_curado/
    variable=precipitacion/
      fuente=s54a-sgyg/
        consolidacion=cierre_precipitacion_2024_2025_v2/

  geografia_curada/
    canonica=estaciones_precipitacion_2024_2025_v3/
      estaciones_municipio.parquet
      divipola_municipios.parquet
      manifest.json
```

El clima aporta 48 particiones y 53.128 filas estacion-dia. La geografia
habilita 116 estaciones canonicas en 84 municipios. Las nueve estaciones en
revision y la exclusion de Bogota permanecen fuera de la agregacion.

## Regla v1

`precipitacion_municipio_dia_v1` aplica estas decisiones:

1. Construye todos los dias de 2024-2025 para los 239 municipios objetivo.
2. Una estacion se considera esperada solo entre `fecha_inicio_clima` y
   `fecha_fin_clima`.
3. Solo cuentan valores `precipitacion_diaria_mm` aceptados por el paso 05.
4. Calcula mediana, media, minimo, maximo, desviacion estandar, cuartiles, IQR
   y rango entre estaciones.
5. Publica `precipitacion_municipal_mm` como la mediana no ponderada cuando al
   menos 50 % de las estaciones esperadas tienen un valor aceptado.
6. Conserva `NaN` cuando no hay evidencia suficiente. No imputa y no interpreta
   ausencia como cero.

La mediana es una eleccion piloto robusta frente a estaciones extremas. No se
presenta como una interpolacion espacial ni como precipitacion areal definitiva.
La media se conserva para medir sensibilidad antes del paso 08.

## Estados municipio-dia

| Estado | Interpretacion | Valor principal |
|---|---|---|
| `SIN_ESTACIONES_CANONICAS` | El municipio no tiene red canonica | `NaN` |
| `SIN_ESTACIONES_ESPERADAS_EN_FECHA` | Tiene red, pero ninguna estacion cubre esa fecha | `NaN` |
| `SIN_DATOS_ACEPTADOS` | Habia estaciones esperadas, pero ningun valor supero 05 | `NaN` |
| `COBERTURA_INSUFICIENTE` | Hay datos, pero cubren menos de 50 % de la red esperada | `NaN` |
| `VALIDO_UNA_ESTACION` | La cobertura supera la regla con un valor | Mediana, igual al valor |
| `VALIDO_MULTIESTACION` | La cobertura supera la regla con dos o mas valores | Mediana no ponderada |

`precipitacion_media_estaciones_mm` y las demas estadisticas descriptivas se
conservan aun cuando la cobertura es insuficiente. Esto permite auditar el
descarte sin convertir ese diagnostico en el valor canonico.

## Salida

```text
eco2026_processed/
  clima_municipal/
    variable=precipitacion/
      fuente=s54a-sgyg/
        agregacion=precipitacion_municipio_dia_2024_2025_v1/
          departamento=BOYACÁ/anio=2024/mes=01/
            precipitacion_municipio_dia.parquet
          ...
          resumen_municipios.parquet
          cobertura_municipal_diaria.html
          AgregacionMunicipal_precipitacion_2024_2025.md
          manifest.json
```

El producto principal contiene 48 particiones, una por departamento, ano y mes.
La llave es `codigo_municipio + fecha`.

## Corrida oficial en Colab

La ejecucion oficial termino el 29 de julio de 2026 en 51,64 segundos con el
commit `e76b1f6d00f94a998325e66499e75ddea3b488f0`. Produjo:

- 174.709 filas: 239 municipios por 731 dias.
- 84 municipios con al menos una estacion canonica utilizable y 155 sin una
  estacion canonica utilizable en este dataset y periodo.
- 25.856 municipio-dias validos.
- 20.760 filas validas con una estacion y 5.096 multiestacion.
- 11.703 filas con estaciones esperadas, pero sin datos aceptados.
- 92 filas con algun dato y cobertura inferior a 50 %.
- 23.753 filas de municipios con red, pero sin estacion esperada en esa fecha.
- 113.305 filas de municipios sin estaciones canonicas.
- 48 Parquet mensuales, resumen, reporte, grafica y manifiesto persistidos.
- Cero duplicados en la llave `codigo_municipio + fecha`.
- Cero valores principales presentes en estados no validos y cero valores
  nulos en estados validos.

Los 84 municipios representan 35,15 % de los 239 municipios objetivo; los 155
sin estacion canonica utilizable representan 64,85 %. Esta cifra no demuestra
que jamas haya existido una estacion IDEAM en esos municipios: significa que
ninguna estacion del dataset de precipitacion, dentro de 2024-2025, supero
simultaneamente los controles de disponibilidad, calidad y geografia canonica.

Entre los 84 municipios con red, 25.856 de 37.651 dias con alguna estacion
esperada fueron validos, una cobertura agregada de 68,67 %. La cobertura no es
uniforme: Quetame tiene una estacion canonica, pero cero dias aceptados en la
ventana evaluada. Por eso `municipios_con_estacion_canonica` no debe
interpretarse como `municipios_con_serie_completa`.

## Ejecucion segura

1. Abrir `07_ClimateMunicipalAggregator.ipynb` desde `feature/SCRUM-14`.
2. Ejecutar con `EJECUTAR_AGREGACION_MUNICIPAL=False`.
3. Confirmar clima `COMPLETA`, 48 particiones, geografia v3 y 116 estaciones.
4. Mantener `GUARDAR_RESULTADOS=True` y
   `SOBRESCRIBIR_RESULTADOS=False`.
5. Cambiar solo `EJECUTAR_AGREGACION_MUNICIPAL=True`.
6. Ejecutar nuevamente desde la configuracion hasta el final.
7. Volver a dejar la bandera en `False` antes de guardar el notebook.

## Compuerta antes de 08

La integridad estructural y la semantica de `NaN` ya fueron verificadas. La
auditoria oficial esta en
[`climate_audits/07_municipio_diario/auditoria_municipal_precipitacion_2024_2025.md`](climate_audits/07_municipio_diario/auditoria_municipal_precipitacion_2024_2025.md).

Antes de construir indicadores se deben revisar:

- los 92 municipio-dias con cobertura insuficiente;
- los rangos e IQR de municipios multiestacion;
- la sensibilidad de media frente a mediana;
- la cobertura temporal por municipio que finalmente aparezca en EVA.

Solo despues se definen acumulados, dias de lluvia, extremos, rachas y ventanas
semestrales o de ciclo agricola.
