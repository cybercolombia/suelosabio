# Estado vigente del proyecto RAIZ

**Actualizado:** 28 de julio de 2026
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
| Periodo operativo a curar ahora | 2024-2025 completos para las variables aprobadas |
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
- Ejecutar la asignacion geografica v3 y resolver las estaciones que
  contradicen el poligono o quedan fuera de cobertura.
- Definir periodos climaticos compatibles con EVA y con el ciclo de cada cultivo.
- Definir baseline, modelos, validacion temporal y metricas.

## Datos climaticos disponibles

La estructura de Drive contiene 120 particiones mensuales por variable: dos
departamentos, cinco anos y doce meses.

| Variable | Dataset | Crudo 2021-2025 | Auditoria 02 | Reglas diarias | Estado |
|---|---|---:|---|---|---|
| Precipitacion | `s54a-sgyg` | Completo estructuralmente | Boyaca y Cundinamarca; 2021, 2023, 2024 y 2025 | 03-05 completos para 2024-2025 | Curada por estacion-dia |
| Humedad | `uext-mhny` | Completo estructuralmente | Cundinamarca 2025 | Pendientes | Candidata |
| Presion atmosferica | `62tk-nxj5` | Completo estructuralmente | Pendiente | Pendientes | Secundaria |
| Velocidad del viento | `sgfv-3yp8` | Completo estructuralmente | Pendiente | Pendientes | Secundaria |
| Temperatura ambiente | `sbwg-7ju4` | 2024-2025 confirmados estructuralmente | Ambos departamentos; 2024 y 2025 | Piloto v1 auditado; contratos v2 listos para repetir cuatro particiones | Alta utilidad; no escalar aun |
| Temperatura minima | `afdg-3zpb` | 2024-2025 reportados; auditoria confirma 2025 | Ambos departamentos; 2025 | 03 y 04 disponibles; piloto pendiente | Alta utilidad; verificar 2024 |
| Temperatura maxima | `ccvq-rp9s` | 2024-2025 reportados; auditoria confirma 2025 | Ambos departamentos; 2025 | 03 y 04 disponibles; piloto pendiente | Alta utilidad; verificar 2024 |

`Completo estructuralmente` significa que existen las carpetas esperadas; no
garantiza cobertura interna, calidad ni continuidad temporal.

## Otros dominios del repositorio

| Dominio | Evidencia actual | Estado vigente |
|---|---|---|
| Agricultura | `CropData.ipynb`, EVA historica 2006-2018 y fuente UPRA 2019-2025 identificada | La fuente reciente debe curarse en un pipeline nuevo |
| Geografia | Catalogos IDEAM, DIVIPOLA y 239 poligonos municipales validados | V2 verificada: 116 canonicas y 10 no canonicas; v3 separa 9 revisiones y 1 exclusion |
| Suelos | `SoilData.ipynb` y cobertura 2020-2024 reportada | Exploratorio; no integrado al alcance analitico actual |
| Meteorologia heredada | `MeteoData.ipynb` | Exploratorio; el pipeline activo esta en `ClimatePipeline/` |

La presencia de un notebook no demuestra que su salida este vigente, curada o
lista para integracion. Estos archivos se revisaran antes de reutilizarlos.

## Estado del pipeline climatico

| Paso | Producto | Estado actual |
|---|---|---|
| 01 Descarga | `clima_crudo` | Validado para cuatro variables disponibles |
| 02 Auditoria cruda | Evidencia para reglas por variable | Precipitacion y temperatura con evidencia; otras desiguales |
| 03 Diario por sensor | `clima_diario_sensor` | Precipitacion 2024-2025 completa; temperatura ambiente tiene piloto v1 completo y requiere repetir cuatro particiones con v2 |
| 04 Auditoria diaria | `auditorias_clima_diario` | Precipitacion validada; piloto v1 de temperatura ambiente auditado y v2 pendiente de corrida |
| 05 Consolidacion | `clima_diario_curado` | Precipitacion 2024-2025 completa y reconciliada |
| Escala operativa | Variables aprobadas 2024-2025 | Precipitacion completa; otras pendientes |
| 06 Geografia | `geografia_curada` | V1 preservada; v2 verificada; v3 pendiente de corrida para excluir Bogota explicitamente |
| 07 Municipio diario | `clima_municipal` | No implementado |
| 08 Indicadores por periodo | `indicadores_climaticos` | No implementado |
| 09 EVA | Agricultura curada | Pendiente de acceso y validacion |
| Dataset maestro y modelo | Tabla analitica y artefactos | No iniciado |

## Regla para nuevas variables

El notebook 02 diagnostica la variable cruda y produce evidencia. No define ni
aplica reglas automaticamente. A partir de esa evidencia se crea y prueba un
contrato propio para la variable antes de habilitarla en 03, 04 y 05.

La infraestructura de rutas, particiones, manifiestos y escritura segura puede
reutilizarse. Las reglas semanticas no: precipitacion se acumula, mientras que
temperatura, humedad, presion y viento necesitan sus propias agregaciones,
umbrales y criterios de calidad.

## Prioridades actuales

1. Repetir con los contratos v2 las cuatro particiones piloto de temperatura
   ambiente de enero-febrero de 2025 antes de definir su consolidacion.
2. Curar las variables adicionales aprobadas para 2024-2025; precipitacion ya
   termino 03-05 y 2021-2023 quedan como ampliacion posterior.
3. Ejecutar auditorias 02 suficientes para las variables adicionales que el
   equipo quiera evaluar y decidir si justifican su incorporacion.
4. Ejecutar el paso 06 v3 y resolver las nueve revisiones espaciales; Bogota
   permanece trazable como exclusion de alcance.
5. Definir uno o dos cultivos y la correspondencia entre periodo agricola y
   ventanas climaticas.
6. Implementar 07 y 08 solo despues de cerrar la asignacion geografica canonica.

El orden completo y sus compuertas se mantienen en
[`project_roadmap.md`](project_roadmap.md). Las rutas y dependencias entre
productos se mantienen en [`data_artifacts.md`](data_artifacts.md). El avance
paso a paso de cada variable se actualiza en
[`climate_pipeline_status/README.md`](climate_pipeline_status/README.md).

## Alcances anteriores

Las expresiones `una variable`, `dos dias restantes`, `entrega del martes` y
`papa + precipitacion` pertenecen a planes de contingencia anteriores. Sirven
como contexto, pero no son decisiones vigentes salvo que se ratifiquen aqui.
