# Ciclo de datos de cultivos

**Actualizado:** 30 de julio de 2026
**Territorio:** Boyacá y Cundinamarca

## Diferencia fundamental frente al clima

EVA no publica una serie diaria. Cada registro corresponde a un municipio, un
cultivo y un período agrícola anual o semestral. Por eso el pipeline no inventa
fechas diarias: normaliza y consolida la frecuencia original.

```text
01.2 descarga EVA
  → 02.2 auditoría cruda
  → 09 curación y cálculo auditable del rendimiento
  → 09.2 auditoría curada
  → agregado municipio × cultivo × período
  → cambios interanuales y cruce geográfico
```

## Fuentes y usos

| Fuente | Ventana | Uso |
|---|---|---|
| API Socrata `uejq-wxrr` | 2022–2024 en el artefacto ejecutado | Auditoría, curación, mapas y cambios de área |
| Excel oficial UPRA `20260526_BaseAgricola20192025.xlsx` | 2019–2025 | Dataset definitivo y pronóstico 2026 |

El Excel 2019–2025 resolvió la limitación temporal del descargador Socrata para
el modelado. Ambos pasan por la misma regla de agregado municipal; no se mezclan
filas de fuentes distintas en una misma llave sin identificación.

## Descarga y auditoría cruda

La descarga conserva departamento, municipio, código DANE, cultivo, año,
período, ciclo, estado físico, áreas, producción y rendimiento publicado. La
auditoría revisa:

- esquema y conversión numérica;
- cobertura por departamento, año, período y cultivo;
- correspondencia de códigos DANE;
- valores nulos, negativos o no finitos;
- área cosechada mayor que sembrada;
- producción con área cosechada no positiva;
- llaves repetidas por ciclo, estado físico o desagregación;
- diferencia entre rendimiento publicado y
  `producción / área cosechada`.

Una auditoría terminada puede quedar con revisión pendiente. Ese estado no
autoriza sumar taxonomías incompatibles.

## Limpieza y homogeneización

Las etiquetas se normalizan sin perder el texto fuente. Los períodos se
clasifican como:

- `A`: primer semestre;
- `B`: segundo semestre;
- `ANUAL`: cultivo o reporte anual.

Solo se agrupan filas con ciclo y estado físico compatibles. Las combinaciones
incompatibles van a `exclusiones.parquet` o
`incidencias_agregacion.parquet`, con motivo trazable.

La llave final es:

```text
codigo_municipio + anio + tipo_periodo + cultivo
```

Las áreas y la producción se suman. El rendimiento no se promedia de forma
simple: se recalcula con totales compatibles.

```text
rendimiento_t_ha =
    produccion_total_t / area_cosechada_total_ha
```

Solo se calcula cuando el área cosechada es positiva. De este modo una finca o
desagregación pequeña no pesa igual que una grande.

## Agregado municipal ejecutado

La versión `cultivo_municipio_periodo_v1` produjo:

| Resultado | Cantidad |
|---|---:|
| Filas de entrada | 14.962 |
| Filas municipio × cultivo × período | 13.692 |
| Comparaciones interanuales | 9.377 |
| Municipios enlazados con geometría | 239 |
| Incidencias ciclo-período excluidas del agregado | 43 |
| Targets con múltiples desagregaciones marcados | 1.159 |

Las comparaciones emparejan A con A, B con B y anual con anual. Para cada par de
años se calculan diferencia absoluta y cambio porcentual de:

- área sembrada;
- área cosechada;
- rendimiento.

Cada medida conserva su propio universo de validez. Un registro puede ser válido
para área sembrada y no para rendimiento.

## Por qué no se llevó cultivos a día

Interpolar un rendimiento semestral a 181 o 184 días produciría muchos valores
artificiales y no agregaría información. La unión con clima se hace en la
dirección científicamente válida:

1. el clima conserva su detalle diario;
2. se calculan indicadores dentro de cada semestre;
3. esos indicadores se unen a la observación agrícola del mismo municipio,
   año y período.

Así ambos dominios llegan a una llave comparable sin alterar la frecuencia
original del target.

## Controles para modelado

- Producción y área cosechada se conservan para auditar el target.
- No entran como predictores: juntas revelan exactamente el rendimiento.
- Para pronosticar 2026 solo se usan áreas sembradas rezagadas, nunca el área
  futura.
- La selección de municipios usa área sembrada 2024–2025 y cobertura histórica,
  no el rendimiento 2026.
- El cambio metodológico de EVA desde 2022 se conserva como riesgo documental;
  la validación temporal mide su impacto indirectamente.

## Artefactos

- `agricultura_curada/version=eva_curada_v1/`
- `auditorias_agricultura/capa=eva_curada/`
- `agricultura_municipal/version=cultivo_municipio_periodo_v1/`
- `crop_forecasting/datasets/version=papa_rendimiento_2026_v1/`

La especificación física de cada archivo está en
[`../data_artifacts.md`](../data_artifacts.md).
