# Estrategia exploratoria para datos climaticos

**Estado:** referencia metodologica vigente
**Alcance y fases:** [`project_status.md`](project_status.md) y
[`project_roadmap.md`](project_roadmap.md)

La secuencia operativa, sus compuertas de calidad y la politica de datos
faltantes se mantienen en
[`climate_pipeline_guide.md`](climate_pipeline_guide.md).

Este documento resume una estrategia inicial para trabajar variables climaticas en el
proyecto RAIZ. No define todavia el dataset maestro agricola ni el modelo final:
su objetivo es ordenar la exploracion antes de reducir o integrar datos.

## Contexto

Algunos datasets climaticos de datos.gov.co pueden contener observaciones
subdiarias por estacion meteorologica. Esto explica que existan millones de
registros incluso para una sola variable, como precipitacion.

Antes de conectar estos datos con rendimiento agricola, conviene entender:

- Cobertura temporal por dataset.
- Cobertura geografica por departamento, municipio y estacion.
- Frecuencia real de observacion.
- Calidad de datos, duplicados y valores faltantes.
- Diferencias entre datasets aparentemente similares.
- Variables y sensores disponibles.

## Capas de trabajo

Los nombres fisicos y contratos vigentes se detallan en
[`data_artifacts.md`](data_artifacts.md). Las siguientes capas explican su
proposito conceptual.

### 1. Datos crudos

Son los datos tal como vienen de la fuente. Pueden estar a nivel de estacion y
timestamp subdiario.

Uso principal:

- Auditoria de fuente.
- Reproducibilidad.
- Verificacion de frecuencia, sensores y cobertura.

### 2. Dataset climatico exploratorio

Conserva bastante detalle, pero ya puede estar normalizado en columnas basicas:
estacion, fecha, departamento, municipio, variable, valor, unidad y fuente.

Uso principal:

- Graficas de cobertura temporal.
- Conteo de estaciones activas.
- Series de tiempo por estacion.
- Mapas de estaciones.
- Distribucion de valores observados.
- Comparacion entre fuentes similares.

### 3. Dataset climatico agregado

Reduce la granularidad subdiaria a periodos utiles: diario, mensual, semestral o
anual, segun la variable y el objetivo analitico.

Uso principal:

- Preparar variables climaticas interpretables.
- Reducir volumen de datos.
- Facilitar cruces posteriores con cultivos.
- Medir cobertura y calidad por periodo.

### 4. Dataset maestro agricola

Esta capa debe construirse despues de entender las fuentes climaticas y agricolas.
Una posible unidad de analisis futura es municipio + periodo + cultivo.

Uso principal:

- Modelado predictivo.
- Analisis de relacion entre clima, suelo y rendimiento agricola.

## Agregaciones climaticas candidatas

Las agregaciones deben depender de la variable. Para precipitacion, por ejemplo,
la suma suele ser mas informativa que el promedio.

Variables derivadas candidatas:

- Precipitacion total diaria, mensual, semestral o anual.
- Dias con lluvia.
- Dias secos consecutivos.
- Precipitacion maxima diaria.
- Percentiles de precipitacion, como p95 o p99.
- Numero de observaciones validas por periodo.
- Porcentaje de cobertura esperada por estacion y periodo.
- Temperatura media, minima y maxima por periodo.
- Humedad relativa media y percentiles por periodo.
- Indicadores de eventos extremos.

### Reduccion diaria a municipio-periodo

La capa diaria no se reemplaza: se conserva como fuente trazable y se construye
otra tabla de caracteristicas. El orden correcto evita que una estacion con mayor
frecuencia o cobertura reciba mas peso:

```text
estacion-sensor-dia -> estacion-dia -> municipio-dia -> municipio-periodo
```

| Variable | Agregaciones candidatas por semestre o periodo |
|---|---|
| Precipitacion | Total, dias con lluvia, intensidad media en dias lluviosos, p95/p99, maximo 1/3/5/7 dias, racha seca y racha humeda |
| Temperatura | Media, minima, maxima, desviacion, p10/p90, dias frios/calientes, grados-dia y rachas extremas |
| Humedad relativa | Media, minima, maxima, desviacion, p10/p90, dias bajo/sobre umbral y persistencia |
| Presion atmosferica | Media, desviacion, rango, p05/p95 y cambios diarios; interpretar el nivel junto con altitud |
| Velocidad del viento | Media, maxima, p90/p95/p99, dias fuertes, dias de calma y persistencia |

Todas las variables deben conservar dias esperados, dias observados, porcentaje
de cobertura, brecha consecutiva maxima, estaciones utilizadas y calidad del
periodo. No se corrige una suma incompleta multiplicandola automaticamente por el
inverso de la cobertura.

Para no esconder la distribucion temporal dentro del semestre, se conserva un
perfil mensual o bloques inicio-mitad-fin. El semestre calendario se usa solo si
coincide con `Periodo` de EVA; cuando exista informacion del cultivo se deben
evaluar tambien ventanas de siembra, desarrollo y cosecha.

## Formato recomendado para datos procesados

Para datasets grandes se recomienda usar Parquet en lugar de CSV.

Ventajas:

- Mejor compresion.
- Lectura mas rapida para analitica.
- Conserva tipos de datos.
- Permite leer solo columnas necesarias.
- Funciona bien con particiones por fuente, departamento y periodo.

Ejemplo de estructura:

```text
eco2026_processed/
  clima_crudo/
    variable=precipitacion/
      fuente=s54a-sgyg/
        departamento=CUNDINAMARCA/
          anio=2026/
            mes=01/
              part-00000.parquet
```

Esta estructura permite trabajar en Colab con subconjuntos manejables sin cargar
todo el pais o todos los anos en memoria.

## Visualizaciones exploratorias sugeridas

- Registros por ano y mes.
- Estaciones activas por departamento.
- Cobertura temporal por estacion.
- Mapa de estaciones.
- Serie de tiempo para estaciones seleccionadas.
- Distribucion de valores observados.
- Comparacion entre datasets por fecha, estacion y valor.
- Porcentaje de datos faltantes o cobertura incompleta.

## Regla operativa para exploraciones

La API de datos.gov.co/Socrata debe usarse principalmente para diagnosticos
pequenos. Para evitar consultas pesadas, cualquier exploracion directa contra la
API debe filtrar por:

- Departamento.
- Estacion meteorologica.
- Ventanas cortas de tiempo, idealmente cinco dias o menos.

Incluso con filtros por departamento, algunas consultas siguen siendo inviables
si requieren agregados sobre muchos registros, por ejemplo `distinct`, `count(*)`
o agrupaciones amplias. Esas consultas pueden generar timeouts o tiempos poco
confiables.

Los departamentos priorizados para el proyecto son:

- Cundinamarca.
- Boyaca.

Decision operativa: para analisis exploratorios serios se deben descargar los
datos de los dos departamentos priorizados a Parquet y auditar localmente sobre
esos archivos. La descarga debe hacerse por particiones controladas, por ejemplo
departamento + ano + mes.

Las primeras auditorias sobre Parquet deben revisar:

- Rango temporal descargado.
- Numero de archivos y filas por particion.
- Estaciones y sensores presentes.
- Duplicados por estacion, sensor y fecha de observacion.
- Frecuencia temporal entre observaciones.
- Distribucion de valores observados.

## Auditoria diagnostica y secuencia de limpieza

La auditoria de datos climaticos crudos debe ser de solo lectura. Su objetivo es
producir evidencia y recomendaciones para el procesamiento, no corregir los
Parquet originales. Los hallazgos deben distinguir entre problemas criticos,
advertencias e informacion descriptiva.

La frecuencia no se debe inferir solamente a partir del numero de registros por
estacion. Debe calcularse con las diferencias entre timestamps consecutivos para
cada combinacion de `codigoestacion` y `codigosensor`, porque una misma estacion
puede contener sensores con cadencias diferentes.

Antes de construir registros diarios se debe diagnosticar y definir reglas para:

- Tipos de datos, unidades y fechas no interpretables.
- Nulos y valores fisicamente sospechosos.
- Duplicados exactos.
- Duplicados de clave con el mismo valor.
- Conflictos con igual estacion, sensor y fecha pero valores diferentes.
- Cambios de municipio, coordenadas o unidad dentro de una estacion o sensor.
- Frecuencia observada y cobertura minima necesaria para considerar valido un dia.

Las reglas de agregacion diaria dependen de la variable y no pertenecen a la
auditoria generica. Tampoco se deben imputar observaciones subdiarias antes de
agregar sin una justificacion especifica: esto podria fabricar precipitacion,
alterar promedios o esconder fallas de cobertura. Los dias faltantes y la
continuidad se evaluan de nuevo despues de construir la capa diaria. Cualquier
imputacion posterior debe conservar una bandera de calidad y evitar fuga temporal
durante el modelado.

### Responsabilidad de cada notebook del pipeline

```text
01 descarga -> 02 auditoria cruda -> reglas por variable
            -> 03 diario por sensor -> 04 auditoria diaria
            -> 05 diario consolidado por estacion -> 06 geografia
            -> 07 agregado municipal -> 08 indicadores por periodo
```

- `01_Climate_Precipitation_DataDownloader.ipynb` conserva las observaciones crudas
  particionadas por departamento, ano y mes.
- `02_Climate_Precipitation_DataAudit.ipynb` diagnostica la fuente cruda. Sus hallazgos sobre
  unidad, cadencia, duplicados, conflictos, geografia y rangos permiten proponer
  un contrato distinto para cada variable; no modifica los datos.
- `03_Climate_Precipitation_DailyProcessor.ipynb` aplica las reglas preliminares de la variable
  y produce una fila por estacion, sensor y dia.
- `04_Climate_Precipitation_DailyAudit.ipynb` revisa el resultado diario preliminar. Evalua
  ausencias, cobertura, extremos y sensores paralelos para confirmar o ajustar
  el contrato.
- `05_Climate_Precipitation_DailyConsolidator.ipynb` aplica el contrato versionado y produce
  una fila canonica por estacion y dia.
- `06_Climate_Precipitation_GeographyAudit.ipynb` audita estaciones y DIVIPOLA, produce el mapa
  de puntos y deja explicitas las asignaciones que requieren poligonos.
- El futuro `07_Climate_Precipitation_MunicipalAggregator.ipynb` solo debe ejecutarse cuando el
  historico diario consolidado y la asignacion estacion-municipio esten
  validados.
- El futuro paso 08 construira indicadores municipio-periodo sin reemplazar las
  capas diarias trazables.

La infraestructura de lectura, particiones, manifiestos y escrituras seguras es
reutilizable. Las reglas semanticas no lo son automaticamente: precipitacion se
acumula, mientras que temperatura, humedad, presion y viento requieren analizar
y definir sus propias agregaciones y controles.

## Nota preliminar sobre precipitacion

Los datasets `s54a-sgyg` y `m84s-22dd` tienen columnas muy similares para
precipitacion. En consultas exploratorias pequenas, filtradas por estacion y
ventanas de cinco dias entre 2017 y 2026, ambos datasets mostraron datos
practicamente equivalentes en las muestras historicas consultadas de Cundinamarca,
Boyaca y Antioquia. El alcance actual del proyecto se limita a Cundinamarca y
Boyaca.

La principal diferencia observada hasta ahora es temporal:

- `s54a-sgyg` inicia en 2003.
- `m84s-22dd` inicia en 2017.

En una muestra de Antioquia al inicio de 2017, `s54a-sgyg` incluyo un registro
inicial adicional frente a `m84s-22dd`. En otras muestras posteriores, las
primeras filas comparadas coincidieron entre ambos datasets.

Decision actual: para el proyecto se escoge `s54a-sgyg` como fuente principal de
precipitacion por su mayor cobertura historica. El dataset `m84s-22dd` se
considera un probable duplicado o subconjunto desde 2017 y no se usara como
fuente principal, salvo como referencia de validacion si hiciera falta.

## Riesgo critico: frecuencia irregular

Aunque los datasets de precipitacion parezcan equivalentes entre si, la data
cruda no debe agregarse de forma ingenua. En muestras exploratorias se observaron
frecuencias distintas segun estacion o periodo:

- Algunas estaciones reportan cada 10 minutos.
- Otras estaciones pueden reportar cada 1 minuto.
- En algunos casos puede haber multiples sensores o registros con frecuencia
  mayor a la esperada.

Esto puede sesgar analisis si se calcula una media simple sobre todos los
registros crudos, porque una estacion con mas observaciones por hora tendria mas
peso que otra.

Antes de construir agregaciones climaticas se debe auditar:

- Frecuencia real por estacion y periodo.
- Duplicados por estacion, sensor y fecha de observacion.
- Sensores disponibles por estacion.
- Cobertura esperada frente a cobertura observada.
- Interpretacion correcta de `valorobservado` para precipitacion.

Para precipitacion, la hipotesis de trabajo es construir primero una capa diaria
por estacion y conservar conteos y metricas de cobertura. La suma diaria solo es
valida si se confirma que `valorobservado` representa incrementos comparables y
no un acumulado del sensor. Esta semantica debe validarse con la documentacion de
la fuente, las unidades y los patrones observados en los datos.

El procesamiento preliminar se detalla en
[`climate_daily_processing.md`](climate_daily_processing.md). El contrato
estacion-dia ya validado, incluida la ventana de cobertura, se documenta en
[`climate_daily_consolidation.md`](climate_daily_consolidation.md).
