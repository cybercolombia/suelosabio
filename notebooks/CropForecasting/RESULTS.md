# Resultados del pronóstico de rendimiento de papa 2026

**Versión:** `papa_rendimiento_2026_v1`

**Fecha de corte climática:** 30 de julio de 2026

**Territorio:** 10 municipios de Boyacá y 10 de Cundinamarca

## Resultado principal

El modelo con menor MAE reciente fue el baseline temporal que usa el último
rendimiento conocido del mismo municipio y semestre. En los backtests de 2024 y
2025 obtuvo:

| Modelo | Representación | MAE (t/ha) | RMSE (t/ha) | R² | sMAPE |
|---|---|---:|---:|---:|---:|
| Último rendimiento | `lag_1` | **2,302** | 3,965 | 0,276 | 9,50 % |
| Ridge | `one_hot_entity` | 2,680 | **3,856** | **0,323** | 10,91 % |
| Ridge | `geo_history` | 2,739 | 3,973 | 0,289 | 11,20 % |
| Random Forest | `geo_history` | 2,748 | 3,977 | 0,297 | 11,05 % |
| Extra Trees | `geo_history` | 2,750 | 4,044 | 0,269 | 11,00 % |
| MLP | `geo_history` | 4,204 | 5,323 | -0,314 | 16,86 % |

La métrica primaria definida por el proyecto es MAE. Por ello se conserva el
baseline como modelo final, aunque Ridge obtuvo RMSE y R² ligeramente mejores.
Forzar una red neuronal o un ensamble habría empeorado el error absoluto esperado.

## Evaluación temporal del ganador

| Año de prueba | Filas | MAE | RMSE | R² | sMAPE |
|---:|---:|---:|---:|---:|---:|
| 2021 | 40 | 2,835 | 4,650 | 0,000 | 11,65 % |
| 2022 | 40 | 2,579 | 4,062 | 0,231 | 10,71 % |
| 2023 | 40 | 2,091 | 3,166 | 0,447 | 9,22 % |
| 2024 | 40 | 1,708 | 3,796 | 0,125 | 7,26 % |
| 2025 | 40 | 2,895 | 4,135 | 0,428 | 11,74 % |
| **Global 2021–2025** | **200** | **2,422** | **3,991** | **0,276** | **10,12 %** |

El desempeño es más débil en Cundinamarca-B: MAE 3,261 t/ha y R² -0,221.
Esa desagregación debe mostrarse siempre junto al resultado global.

## Representación y embeddings

No hay texto libre que justifique embeddings semánticos. Se evaluaron dos
representaciones tabulares:

- `one_hot_entity`: municipio, departamento y semestre codificados one-hot.
- `geo_history`: departamento y semestre one-hot; el municipio se representa por
  latitud, longitud, rezagos de rendimiento y área sembrada histórica.

La red MLP con representación `geo_history` fue claramente inferior. El tamaño y
la longitud de la serie (siete años EVA) no justifican embeddings neuronales de
entidad. El baseline ganador solo consume `rendimiento_lag_1`; los otros features
se conservan en el dataset para auditoría y futuros reentrenamientos.

## Pronóstico 2026

| Departamento | Semestre | Municipios | Media (t/ha) | Mediana | Mínimo | Máximo |
|---|---|---:|---:|---:|---:|---:|
| Boyacá | A | 10 | 22,58 | 20,21 | 18,45 | 35,00 |
| Boyacá | B | 10 | 24,27 | 21,91 | 18,79 | 39,85 |
| Cundinamarca | A | 10 | 26,43 | 24,73 | 19,82 | 35,00 |
| Cundinamarca | B | 10 | 25,58 | 24,86 | 17,00 | 32,79 |

Los 40 registros detallados se materializan como `pronostico_2026.csv` y
`pronostico_2026.parquet` en
`eco2026_processed/crop_forecasting/models/version=papa_rendimiento_2026_v1/`.

## Clima 2026 y cautelas

- 2026-A usa 181 días climáticos observados.
- 2026-B usa 27 días observados y 157 días de climatología 2019–2025.
- NASA POWER aún no tenía datos válidos del 28 al 30 de julio al momento de la
  ejecución; esos días se clasificaron como climatología, no como observaciones.
- Los intervalos son bandas empíricas construidas con el percentil 90 del error
  absoluto del backtesting. No son intervalos probabilísticos calibrados.
- EVA 2026 todavía no contiene el target real. Las métricas pertenecen al
  backtesting 2021–2025, no al pronóstico 2026.

Fuentes: [EVA 2025 de UPRA](https://upra.gov.co/es-co/eva/eva-2025) y
[NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/).
