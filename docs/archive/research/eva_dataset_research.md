# Investigación rápida: dataset agrícola EVA actualizado

**Fecha de verificación:** 11 de julio de 2026

> **Estado:** investigación histórica conservada como evidencia. La fuente y el
> cultivo finales están documentados en
> [`data_pipeline/agriculture.md`](../../data_pipeline/agriculture.md) y
> [`data_pipeline/forecast.md`](../../data_pipeline/forecast.md).

## Conclusión

El dataset `2pnw-mmge` no es la fuente agrícola más reciente. Su cobertura real
es 2006–2018 y contiene 206.068 filas. Ese número coincide exactamente con las
206.068 filas observadas en `EvaluacionAgro_EVA_2026.csv`, por lo que el nombre
del archivo en Drive parece indicar la fecha de descarga o preparación, no el año
de las observaciones.

Existen dos reemplazos oficiales más actuales:

1. **Datos.gov.co:** EVA 2019–2024, recurso `uejq-wxrr`.
2. **UPRA:** Base Agrícola EVA 2019–2025, publicada como Excel oficial en mayo de
   2026.

Para el MVP se recomienda usar la base de UPRA 2019–2025 como fuente agrícola
principal. La base 2006–2018 puede conservarse como histórico, pero no conviene
convertir su armonización en una dependencia de la entrega.

## Fuentes oficiales

### Base recomendada: UPRA 2019–2025

- [Página EVA 2025 de UPRA](https://upra.gov.co/es-co/eva/eva-2025)
- [Descarga directa Base Agrícola 2019–2025](https://upra.gov.co/sites/default/files/2026-05/20260526_BaseAgricola20192025.xlsx)

La página de UPRA documenta que la operación cubre producción, área sembrada,
área cosechada y rendimiento municipal. Para cultivos transitorios se recopilan
los semestres A y B; los cultivos permanentes tienen reporte anual.

### API útil: datos.gov.co 2019–2024

- [Página EVA 2019–2024](https://www.datos.gov.co/Agricultura-y-Desarrollo-Rural/Evaluaciones-Agropecuarias-Municipales-EVA-2019-20/uejq-wxrr)
- API: `https://www.datos.gov.co/resource/uejq-wxrr.json`

Esta API es útil para consultas y para el perfilador, pero al 11 de julio de 2026
termina en 2024. La descarga de UPRA ya incorpora 2025 y revisiones menores de
años anteriores.

### Base histórica 2006–2018

- Recurso: `2pnw-mmge`
- API: `https://www.datos.gov.co/resource/2pnw-mmge.json`

Debe tratarse como fuente histórica, no como fuente agrícola vigente.

## Resultados verificados

### EVA UPRA 2019–2025

Se leyó en memoria la hoja `BasePagina` con `header=8`.

- Dimensiones: 166.733 filas y 18 columnas.
- Cobertura: 2019–2025.
- Municipios nacionales: 1.103.
- Cultivos: 166.
- Rendimientos nulos: 0 % en la columna publicada.

Filas por año:

| Año | Filas |
|---:|---:|
| 2019 | 20.436 |
| 2020 | 21.511 |
| 2021 | 23.898 |
| 2022 | 24.808 |
| 2023 | 24.909 |
| 2024 | 25.554 |
| 2025 | 25.617 |

Cobertura del territorio propuesto:

| Departamento | Filas | Años | Municipios | Cultivos | Filas 2025 | Rendimientos válidos |
|---|---:|---|---:|---:|---:|---:|
| Boyacá | 17.679 | 2019–2025 | 123 | 104 | 2.709 | 17.679 |
| Cundinamarca | 15.585 | 2019–2025 | 116 | 110 | 2.361 | 15.585 |

### EVA datos.gov.co 2019–2024

Consulta directa al recurso `uejq-wxrr`:

- Cobertura: 2019–2024.
- Filas: 141.073.
- Boyacá: 14.969 filas.
- Cundinamarca: 13.218 filas.

### EVA histórica 2006–2018

Consulta directa al recurso `2pnw-mmge`:

- Cobertura: 2006–2018.
- Filas: 206.068.

## Columnas de la base UPRA 2019–2025

```text
Código Dane departamento
Departamento
Código Dane municipio
Municipio
Desagregación cultivo
Cultivo
Ciclo del cultivo
Grupo cultivo
Subgrupo
Año
Periodo
Área sembrada (ha)
Área cosechada (ha)
Producción (t)
Rendimiento (t/ha)
Nombre científico del cultivo
Código del cultivo
Estado físico del cultivo
```

Las variables principales de la base vieja tienen equivalentes claros en la
nueva. Sin embargo, cambian nombres, tipos y taxonomías; no se deben concatenar
los archivos sin una capa de homologación.

## Cultivos con cobertura continua en ambos departamentos

Se buscaron cultivos presentes durante los siete años en Boyacá y Cundinamarca.
Los primeros resultados por cantidad de rendimientos válidos fueron:

| Cultivo | Filas | Municipios sumados entre departamentos | Años mínimos por departamento |
|---|---:|---:|---:|
| Maíz | 3.468 | 221 | 7 |
| Papa | 3.006 | 157 | 7 |
| Arveja | 2.165 | 172 | 7 |
| Frijol | 2.064 | 169 | 7 |
| Tomate | 1.555 | 121 | 7 |
| Yuca | 1.118 | 102 | 7 |
| Cebolla de bulbo | 990 | 81 | 7 |
| Aguacate | 843 | 117 | 7 |
| Café | 838 | 123 | 7 |
| Caña | 816 | 113 | 7 |

Esto no decide automáticamente el cultivo. Sí demuestra que maíz y papa son
candidatos fuertes por continuidad, volumen y presencia territorial. La decisión
debe cruzarse con la variable climática que pueda conseguirse y agregarse a
tiempo.

## Importancia productiva en 2025

Se consolidaron las 5.070 filas de Boyacá y Cundinamarca para 2025. Para evitar
promedios de rendimiento engañosos, se sumaron producción y área cosechada por
cultivo y se recalculó el rendimiento ponderado.

La base permite medir impacto **productivo y territorial**, pero no impacto
económico: no contiene precios, costos, empleo ni valor de la producción. Además,
las toneladas de cultivos con estados físicos diferentes no siempre son
directamente comparables.

### Principales cultivos combinados

| Cultivo | Producción (t) | Área cosechada (ha) | Municipios sumados | Rendimiento ponderado (t/ha) |
|---|---:|---:|---:|---:|
| Caña | 3.828.512 | 59.696 | 113 | 64,13 |
| Papa | 3.062.278 | 124.873 | 153 | 24,52 |
| Tomate | 372.017 | 4.816 | 107 | 77,25 |
| Cebolla de bulbo | 166.787 | 6.919 | 75 | 24,10 |
| Zanahoria | 157.116 | 6.091 | 54 | 25,80 |
| Plátano | 108.851 | 13.286 | 99 | 8,19 |
| Tomate de árbol | 100.729 | 5.748 | 86 | 17,52 |

### Mayor área cosechada

| Cultivo | Área cosechada (ha) | Producción (t) | Municipios sumados |
|---|---:|---:|---:|
| Papa | 124.873 | 3.062.278 | 153 |
| Caña | 59.696 | 3.828.512 | 113 |
| Café | 32.114 | 35.804 | 123 |
| Maíz | 23.099 | 38.596 | 220 |
| Frijol | 14.085 | 22.410 | 163 |
| Plátano | 13.286 | 108.851 | 99 |
| Cacao | 12.002 | 7.996 | 57 |
| Arveja | 8.755 | 15.525 | 165 |

### Mayor presencia municipal

| Cultivo | Municipios sumados | Área cosechada (ha) | Producción (t) |
|---|---:|---:|---:|
| Maíz | 220 | 23.099 | 38.596 |
| Arveja | 165 | 8.755 | 15.525 |
| Frijol | 163 | 14.085 | 22.410 |
| Papa | 153 | 124.873 | 3.062.278 |
| Café | 123 | 32.114 | 35.804 |
| Caña | 113 | 59.696 | 3.828.512 |
| Aguacate | 113 | 5.267 | 54.680 |
| Tomate | 107 | 4.816 | 372.017 |

`Municipios sumados` suma municipios únicos dentro de cada departamento; no hay
solapamiento geográfico entre departamentos.

### Lectura por departamento

En Boyacá, caña lidera la producción con 2,04 millones de toneladas y papa ocupa
el segundo lugar con 1,12 millones. Papa está reportada en 91 municipios y tiene
50.601 ha cosechadas.

En Cundinamarca, papa lidera la producción con 1,94 millones de toneladas y
74.272 ha cosechadas, seguida por caña con 1,79 millones de toneladas. Papa está
reportada en 62 municipios.

### Recomendación de cultivo para el MVP

**Papa es el candidato más equilibrado** para estudiar rendimiento y clima:

- Ocupa el primer lugar en área cosechada combinada.
- Ocupa el segundo lugar en producción total.
- Tiene presencia amplia en ambos departamentos.
- Mantiene cobertura completa entre 2019 y 2025.
- Tiene una relación agronómica explicable con temperatura y disponibilidad de
  agua.
- Su importancia no depende únicamente de un rendimiento alto en pocas hectáreas.

Maíz sería la mejor alternativa si se prioriza cobertura territorial: aparece en
220 municipios sumados, pero tiene menor área y producción. Caña lidera toneladas,
pero requiere revisar desagregaciones, estado físico y comparabilidad antes de
usarla como un solo cultivo. Tomate tiene alta producción por hectárea, aunque su
rendimiento puede depender fuertemente de riego, invernaderos y manejo, variables
que EVA no contiene.

## Cautelas metodológicas

### Cambio desde 2022

La propia base UPRA advierte:

- Desde 2022, área cosechada, producción y rendimiento de cultivos transitorios
  corresponden a cosechas efectivas del periodo.
- Antes de 2022, esas variables corresponden a las siembras realizadas en el
  periodo de referencia.

Esto puede crear un quiebre metodológico dentro de la serie 2019–2025. Debe
documentarse y revisarse en las gráficas por año. Un modelo podría aprender parte
del cambio metodológico en vez de una relación climática.

### Cifras revisables

UPRA indica que las cifras de los dos últimos años pueden modificarse por ajustes
de las fuentes. Para la entrega se pueden usar como la publicación oficial más
reciente, pero deben marcarse como susceptibles de revisión.

### Rendimiento y fuga de información

El rendimiento está definido como producción dividida por área cosechada. Si el
target es `Rendimiento (t/ha)`, no deben usarse `Producción (t)` ni `Área
cosechada (ha)` como predictores: contienen directamente la respuesta.

### Granularidad y agregación

Puede haber varias filas para un mismo municipio, cultivo, año y periodo debido
a desagregación, estado físico u otras categorías. Si el MVP consolida a nivel de
cultivo, el rendimiento no debe promediarse sin ponderación. La regla adecuada es
sumar producción, sumar área cosechada y recalcular:

```text
rendimiento consolidado = producción total / área cosechada total
```

Esta operación sirve para construir el target, pero esas dos columnas no deben
permanecer después como features del modelo.

## Recomendacion tecnica actual

1. Usar la Base Agrícola UPRA 2019–2025 como fuente principal del target.
2. Trabajar primero solo Boyacá y Cundinamarca.
3. Conservar papa y maiz como candidatos hasta comparar cobertura y granularidad.
4. Preparar el cruce principal con la ventana comun 2021-2025 y evaluar si el
   cambio metodologico aconseja modelar solo 2022-2025.
5. Reservar la unión con 2006–2018 como mejora posterior, porque exige homologar
   columnas, códigos, cultivos y metodología.
6. Usar separación temporal para evaluar: por ejemplo, entrenar con años
   anteriores y reservar 2024 o 2025 para prueba, documentando que los últimos
   años pueden recibir revisiones.
7. Mostrar una sensibilidad antes y después de 2022 para detectar el posible
   efecto del cambio metodológico.

La seleccion climatica no se cierra aqui. Puede incluir varias familias si cada
una tiene cobertura, reglas validadas y una contribucion evaluable frente al
baseline. La justificacion y las fuentes se detallan en
[Candidatos de variables climaticas](climate_dataset_candidates.md).

## Consecuencia para el proyecto

El target agrícola ya no obliga a detenerse en 2018. La ventana moderna oficial
2019–2025 se cruza con las fuentes climáticas recientes y contiene suficientes
observaciones municipales para un MVP. El cuello de botella pasa a ser escoger y
preparar variables climaticas compatibles, no encontrar rendimiento agricola
actualizado.
