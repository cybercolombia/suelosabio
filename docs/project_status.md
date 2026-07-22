# Estado vigente del proyecto RAIZ

**Actualizado:** 21 de julio de 2026  
**Estado:** vigente  
**Proposito:** fuente de verdad para alcance, datos disponibles y prioridades

Este documento debe leerse antes de planes anteriores, conversaciones o
recomendaciones preparadas para fechas limite ya vencidas.

## Objetivo en descubrimiento

RAIZ busca estudiar y eventualmente predecir rendimiento agricola municipal a
partir de datos abiertos agricolas, climaticos y geograficos. La pregunta final,
el conjunto de predictores y el modelo aun no estan cerrados.

## Alcance confirmado

| Dimension | Decision vigente |
|---|---|
| Departamentos | Boyaca y Cundinamarca |
| Periodo climatico disponible | 2021-2025 |
| Fuente agricola candidata principal | EVA UPRA 2019-2025 |
| Unidad candidata | Municipio + ano + periodo + cultivo |
| Target candidato | Rendimiento en toneladas por hectarea |
| Principio de datos | Crudos inmutables y productos derivados versionados |

Antioquia no forma parte del alcance. Sus resultados anteriores son pruebas
historicas de descarga y rendimiento de la API.

## Decisiones pendientes

- Escoger uno o dos cultivos. Papa y maiz son los candidatos mejor sustentados,
  pero no constituyen todavia una seleccion definitiva.
- Escoger las variables climaticas del modelo. Ya no se presupone que deba ser
  una sola; cada variable debe justificar utilidad, cobertura y calidad.
- Confirmar el archivo EVA compartido, su hoja, granularidad y reglas de
  consolidacion.
- Confirmar DIVIPOLA y la geografia canonica de estaciones y municipios.
- Definir periodos climaticos compatibles con EVA y con el ciclo de cada cultivo.
- Definir baseline, modelos, validacion temporal y metricas.

## Datos climaticos disponibles

La estructura de Drive contiene 120 particiones mensuales por variable: dos
departamentos, cinco anos y doce meses.

| Variable | Dataset | Crudo 2021-2025 | Auditoria 02 | Reglas diarias | Estado |
|---|---|---:|---|---|---|
| Precipitacion | `s54a-sgyg` | Completo estructuralmente | Boyaca y Cundinamarca; 2021, 2023 y 2025 | Piloto 03-04 validado | Prioritaria y lista para escalar |
| Humedad | `uext-mhny` | Completo estructuralmente | Cundinamarca 2025 | Pendientes | Candidata |
| Presion atmosferica | `62tk-nxj5` | Completo estructuralmente | Pendiente | Pendientes | Secundaria |
| Velocidad del viento | `sgfv-3yp8` | Completo estructuralmente | Pendiente | Pendientes | Secundaria |
| Temperatura ambiente/minima/maxima | Fuentes candidatas en el catalogo | No confirmada | Pendiente | Pendientes | Alta utilidad potencial |

`Completo estructuralmente` significa que existen las carpetas esperadas; no
garantiza cobertura interna, calidad ni continuidad temporal.

## Estado del pipeline climatico

| Paso | Producto | Estado actual |
|---|---|---|
| 01 Descarga | `clima_crudo` | Validado para cuatro variables disponibles |
| 02 Auditoria cruda | Evidencia para reglas por variable | Motor generico disponible; cobertura desigual por variable |
| 03 Diario por sensor | `clima_diario_sensor` | Precipitacion validada en cuatro pilotos de 2025 |
| 03_01 Auditoria diaria | `auditorias_clima_diario` | Precipitacion piloto validada |
| 04 Consolidacion | `clima_diario_curado` | Precipitacion piloto validada en Colab |
| Escala historica | Precipitacion 2021-2025 | Pendiente |
| 05 Municipio y periodo | `clima_municipal` e indicadores | No implementado |
| EVA y DIVIPOLA | Agricultura y geografia curadas | Pendiente de acceso y validacion |
| Dataset maestro y modelo | Tabla analitica y artefactos | No iniciado |

## Regla para nuevas variables

El notebook 02 diagnostica la variable cruda y produce evidencia. No define ni
aplica reglas automaticamente. A partir de esa evidencia se crea y prueba un
contrato propio para la variable antes de habilitarla en 03, 03_01 y 04.

La infraestructura de rutas, particiones, manifiestos y escritura segura puede
reutilizarse. Las reglas semanticas no: precipitacion se acumula, mientras que
temperatura, humedad, presion y viento necesitan sus propias agregaciones,
umbrales y criterios de calidad.

## Prioridades actuales

1. Escalar el pipeline validado de precipitacion al periodo 2021-2025.
2. Ejecutar auditorias 02 suficientes para las variables adicionales que el
   equipo quiera evaluar y decidir si justifican su incorporacion.
3. Ubicar y curar EVA y DIVIPOLA sin esperar a terminar todas las variables.
4. Definir uno o dos cultivos y la correspondencia entre periodo agricola y
   ventanas climaticas.
5. Implementar el paso 05 solo cuando exista historia diaria consolidada y una
   geografia canonica defendible.

## Alcances anteriores

Las expresiones `una variable`, `dos dias restantes`, `entrega del martes` y
`papa + precipitacion` pertenecen a planes de contingencia anteriores. Sirven
como contexto, pero no son decisiones vigentes salvo que se ratifiquen aqui.

