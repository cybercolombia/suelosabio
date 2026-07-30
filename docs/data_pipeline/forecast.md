# Dataset y pronóstico de rendimiento de papa 2026

**Versión:** `papa_rendimiento_2026_v1`
**Fecha de corte climática:** 30 de julio de 2026
**Horizonte:** semestres A y B de 2026

## Objetivo

Pronosticar toneladas de papa por hectárea para los diez municipios con mayor
área sembrada elegible de Boyacá y los diez de Cundinamarca.

La papa fue seleccionada porque, dentro de los registros semestrales 2022–2024,
acumuló 373.478,17 hectáreas sembradas en 155 municipios. El siguiente cultivo,
maíz, acumuló 75.073,81 hectáreas. Además, el Excel UPRA ofrece historia
municipal semestral 2019–2025 suficiente para validación temporal.

## Selección territorial

La selección usa exclusivamente:

- área sembrada de papa en 2024–2025;
- presencia en ambos años;
- al menos cuatro observaciones de rendimiento, dos semestres por año.

No utiliza el target 2026. Después se toman los diez primeros por departamento.

## Construcción del dataset

La llave única es:

```text
codigo_municipio + anio + tipo_periodo + cultivo
```

El dataset tiene 2.366 filas y 56 columnas. Incluye:

| Grupo | Columnas | Ejemplos |
|---|---:|---|
| Historia agrícola | 9 | rendimiento del año anterior, promedio histórico, tendencia y área sembrada rezagada |
| Geografía y tiempo | 3 | latitud, longitud e índice de año |
| Clima por semestre | 33 | precipitación, temperatura, humedad, viento, presión, extremos, rachas y bloques |
| Identidad y período | 8 | municipio, departamento, año, semestre y cultivo |
| Control | 2 | fila de pronóstico y municipio objetivo |
| Target | 1 | rendimiento en toneladas por hectárea |

Hay 45 predictores numéricos candidatos: 9 históricos, 3 geográficos-temporales
y 33 climáticos. Las categorías se codifican según la representación evaluada.

No se incluyen producción ni área cosechada como features. Dado que
`rendimiento = producción / área cosechada`, usarlas causaría fuga de
información.

## Clima usado en el modelo

NASA POWER aporta series diarias 2019–2026 de:

- precipitación;
- temperatura ambiente, mínima y máxima;
- humedad;
- velocidad del viento;
- presión atmosférica.

Para cada municipio y semestre se calculan 33 indicadores: acumulados, medias,
desviaciones, máximos, días húmedos, racha seca, días cálidos o fríos, cobertura
y tres bloques temporales.

El semestre 2026A usa 181 días reales. Para 2026B había 27 días reales y 157
días aún futuros a la fecha de corte; esos días usan la climatología diaria
2019–2025. Por eso el resultado B es un escenario observado más climatología,
no una observación completa.

## Representaciones evaluadas

`Categorías binarias` crea una columna 0/1 por municipio, departamento y
semestre. `Geografía + historia` reemplaza la identidad directa del municipio
por latitud, longitud y rezagos, manteniendo departamento y semestre como
categorías.

No se usaron embeddings semánticos: no hay texto libre. Tampoco se justifican
embeddings neuronales de municipio con solo siete años y 20 territorios
objetivo; la red neuronal probada fue inferior.

## Métodos probados

| Método | Idea |
|---|---|
| Último rendimiento | Usa el rendimiento del mismo municipio y semestre del año anterior |
| Promedio histórico | Usa el promedio conocido del municipio y semestre |
| Regresión Ridge | Regresión lineal regularizada para reducir sobreajuste |
| Bosque aleatorio | Promedia muchos árboles construidos con muestras aleatorias |
| Árboles extra | Ensamble de árboles con cortes más aleatorios |
| Gradient boosting | Agrega árboles secuenciales que corrigen errores previos |
| Red neuronal multicapa | Aprende relaciones no lineales tras imputar y escalar |

Se evaluaron nueve combinaciones de método y representación.

## Validación temporal

Cada prueba entrena solo con años anteriores al año evaluado. Se repite para
2021, 2022, 2023, 2024 y 2025. La selección final usa el promedio de 2024–2025,
los años más cercanos al horizonte 2026.

Las métricas son:

- **Error absoluto medio (MAE):** promedio de la distancia absoluta entre valor
  real y pronóstico. Está en toneladas por hectárea y es la métrica primaria.
- **Raíz del error cuadrático medio (RMSE):** penaliza más los errores grandes;
  también está en toneladas por hectárea.
- **Coeficiente de determinación (R²):** proporción de variación explicada. Uno
  es ideal, cero equivale a no mejorar el promedio y un valor negativo es peor.
- **Error porcentual absoluto simétrico (sMAPE):** error porcentual que trata de
  forma equilibrada sobrestimaciones y subestimaciones.

## Selección del método

| Candidato | MAE | RMSE | R² | sMAPE |
|---|---:|---:|---:|---:|
| Último rendimiento | **2,302** | 3,965 | 0,276 | **9,50 %** |
| Ridge, categorías binarias | 2,680 | **3,856** | **0,323** | 10,91 % |
| Ridge, geografía + historia | 2,739 | 3,973 | 0,289 | 11,20 % |
| Bosque aleatorio, geografía + historia | 2,748 | 3,977 | 0,297 | 11,05 % |
| Árboles extra, geografía + historia | 2,750 | 4,044 | 0,269 | 11,00 % |
| Red neuronal, geografía + historia | 4,204 | 5,323 | −0,314 | 16,86 % |

Ganó `último rendimiento` porque tuvo el menor MAE reciente. Ridge consiguió
RMSE y R² ligeramente mejores, pero la regla del proyecto prioriza el error
absoluto esperado. Elegir un modelo más complejo solo por su sofisticación habría
empeorado esa métrica.

## Por qué no se usó una serie de tiempo más robusta

Modelos como ARIMA, Prophet o redes recurrentes suelen necesitar muchas
observaciones regulares por entidad. Aquí cada municipio tiene como máximo
catorce puntos semestrales de target entre 2019 y 2025, hay un cambio
metodológico en EVA y el clima futuro B es parcialmente climatológico. Ajustar
un modelo independiente por municipio sería inestable; agrupar todos como una
sola serie ignoraría diferencias territoriales.

El backtesting mostró además que la persistencia local es una señal fuerte y
difícil de superar. La decisión no afirma que los métodos temporales complejos
sean inferiores en general: afirma que no ganaron o no son identificables con
esta cantidad y estructura de datos.

## Resultado 2026

| Departamento | Semestre | Municipios | Media | Mediana | Mínimo | Máximo |
|---|---|---:|---:|---:|---:|---:|
| Boyacá | A | 10 | 22,58 | 20,21 | 18,45 | 35,00 |
| Boyacá | B | 10 | 24,27 | 21,91 | 18,79 | 39,85 |
| Cundinamarca | A | 10 | 26,43 | 24,73 | 19,82 | 35,00 |
| Cundinamarca | B | 10 | 25,58 | 24,86 | 17,00 | 32,79 |

El backtesting global 2021–2025 del ganador, sobre 200 observaciones, obtuvo MAE
2,422 t/ha, RMSE 3,991 t/ha, R² 0,276 y sMAPE 10,12 %. El segmento más débil es
Cundinamarca-B, con MAE 3,261 t/ha y R² −0,221; debe mostrarse junto al resultado
global.

Las bandas de la salida son el percentil 90 del error absoluto histórico. Son
bandas empíricas, no intervalos probabilísticos calibrados. EVA 2026 todavía no
contiene el target real, por lo que estas métricas describen el backtesting y no
una validación del futuro.
