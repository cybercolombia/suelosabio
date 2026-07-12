# Estrategia exploratoria para datos climaticos

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

## Capas de trabajo propuestas

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
  precipitacion/
    dataset_id=s54a-sgyg/
      departamento=ANTIOQUIA/
        anio=2026/
          part-001.parquet
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
- Antioquia.

Decision operativa: para analisis exploratorios serios se deben descargar los
datos de los tres departamentos priorizados a Parquet y auditar localmente sobre
esos archivos. La descarga debe hacerse por particiones controladas, por ejemplo
departamento + ano + mes.

Las primeras auditorias sobre Parquet deben revisar:

- Rango temporal descargado.
- Numero de archivos y filas por particion.
- Estaciones y sensores presentes.
- Duplicados por estacion, sensor y fecha de observacion.
- Frecuencia temporal entre observaciones.
- Distribucion de valores observados.

## Nota preliminar sobre precipitacion

Los datasets `s54a-sgyg` y `m84s-22dd` tienen columnas muy similares para
precipitacion. En consultas exploratorias pequenas, filtradas por estacion y
ventanas de cinco dias entre 2017 y 2026, ambos datasets mostraron datos
practicamente equivalentes en los departamentos priorizados para el proyecto:
Cundinamarca, Boyaca y Antioquia.

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
por estacion, con suma diaria y conteo de observaciones validas. Esta hipotesis
debe validarse con la documentacion de la fuente y con patrones observados en los
datos.
