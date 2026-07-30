# Ciclo geográfico

**Actualizado:** 30 de julio de 2026
**Sistema de referencia canónico:** EPSG:4326

## Propósito

La geografía evita unir series por nombres ambiguos. El código DANE municipal es
la llave común entre clima, cultivos y pronóstico; la geometría permanece como
dimensión separada para no repetir polígonos en cada fecha.

## Fuentes

| Fuente | Uso |
|---|---|
| Catálogo oficial de estaciones IDEAM | Identidad, nombre y coordenadas de estación |
| DIVIPOLA | Códigos de departamento y municipio |
| `Boyaca_Cundinamarca_Municipios.gpkg` | 239 polígonos municipales |
| Coordenadas NASA POWER | Centroide/celda diaria para el dataset de pronóstico |

Los polígonos fueron validados como geometrías válidas en EPSG:4326 y cubren 123
municipios de Boyacá y 116 de Cundinamarca.

## Auditoría de estaciones

Para cada variable se construye un catálogo único de estaciones observadas. Se
revisan:

- coordenadas nulas o fuera de rango;
- múltiples coordenadas para un mismo código;
- movimiento superior a 100 metros;
- cambios de nombre, municipio o etiqueta;
- pertenencia al territorio objetivo;
- coincidencia con catálogo oficial;
- resultado de punto-en-polígono.

La coincidencia textual con catálogo produce un candidato, no una asignación
canónica automática. La asignación final se basa en código, evidencia oficial y
polígono.

## Productos

| Archivo | Granularidad y función |
|---|---|
| `catalogo_estaciones_climaticas.parquet` | Una fila por estación auditada |
| `divipola_municipios.parquet` | Una fila por código municipal |
| `divipola_municipios_geometria.parquet` | Una geometría por municipio |
| `estaciones_municipio_candidato.parquet` | Cruces aún no aprobados |
| `estaciones_municipio.parquet` | Asignaciones canónicas |
| `estaciones_revision.parquet` | Casos que no entran al agregado |
| `estaciones_excluidas.parquet` | Casos fuera de alcance o invalidados |

En precipitación v3 quedaron 116 asignaciones canónicas, 9 revisiones y 1
exclusión. Las otras variables tienen entre 71 y 82 asignaciones canónicas. Un
municipio sin estación no recibe cero: su serie queda ausente.

## Agregado estación a municipio

El calendario se materializa por municipio y día. En cada fecha se comparan:

1. estaciones canónicas esperadas;
2. estaciones con fila;
3. estaciones con dato aceptado;
4. porcentaje de cobertura;
5. dispersión entre estaciones.

La mediana es el valor municipal principal porque reduce el efecto de una
estación extrema. Media, mínimo, máximo, desviación e intervalo intercuartílico
se conservan para auditoría. La regla no interpola espacialmente municipios sin
red.

## Geografía agrícola y mapas

El agregado agrícola se une a los 239 polígonos por `codigo_municipio`. Los
polígonos no se duplican en el parquet temporal. Para un mapa se cruza:

```text
geometría municipal
  + cultivo_municipio_periodo
  + cambio interanual de la medida seleccionada
```

Debe indicarse siempre si el color representa área sembrada, área cosechada o
rendimiento, junto con años y período comparable.

## Geografía del pronóstico

El pronóstico selecciona diez municipios por departamento. Latitud y longitud
representan el municipio en los modelos tabulares. NASA POWER aporta una celda
diaria por municipio y evita que la ausencia de una estación elimine municipios
del entrenamiento. Esta malla es una fuente climática distinta; no reemplaza la
auditoría de estaciones para usos observacionales locales.
