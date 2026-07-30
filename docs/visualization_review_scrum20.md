# Revisión de visualizaciones geográficas — SCRUM-20

**Actualizado:** 30 de julio de 2026

**Estado:** vigente

**Alcance:** presentación de estaciones, cultivos, agregado municipal y
pronóstico de papa

## Fuentes

- Geometría municipal:
  `Boyaca_Cundinamarca_Municipios.gpkg`, 239 municipios.
- Estaciones: capas canónicas 2024–2025 de las seis variables climáticas.
- Agricultura:
  `cultivo_municipio_periodo.parquet`, versión
  `cultivo_municipio_periodo_v1`.
- Pronóstico:
  `pronostico_2026.parquet`, versión `papa_rendimiento_2026_v1`.

## Mapas incorporados

| Archivo | Medida | Regla |
|---|---|---|
| `10_mapa_estaciones_climaticas.png` | 127 estaciones únicas | Tamaño y color por número de variables con asignación canónica |
| `11_mapa_cultivos_principales.png` | Área sembrada 2022–2024 | Cultivo dominante por municipio entre los diez de mayor área total |
| `12_mapa_agregado_municipal_papa.png` | Área, producción y rendimiento | Totales 2022–2024; rendimiento recalculado con producción y área compatibles |
| `13_mapa_produccion_papa_por_anio.png` | Producción anual | Escala común 2022–2024 y cinco municipios principales por año |
| `14_mapa_pronostico_rendimiento_2026.png` | Rendimiento pronosticado | Escala común por semestre y departamento para los 20 municipios objetivo |

## Criterios de interpretación

- Un municipio sin color no se interpreta como valor cero.
- Área sembrada y producción son medidas distintas; no se sustituyen entre sí.
- La clasificación del cultivo dominante usa área sembrada acumulada, no
  rendimiento.
- Las escalas logarítmicas se aplican a área y producción debido a su asimetría.
- Los mapas de pronóstico representan los resultados del modelo, no valores EVA
  observados para 2026.
- El mapa de estaciones muestra disponibilidad espacial de la red procesada, no
  cobertura diaria suficiente en todos los períodos.

## Reproducción

Los mapas y las demás figuras de presentación se generan con:

```bash
MPLCONFIGDIR=/tmp/suelosabio-matplotlib \
python docs/presentation/generate_presentation_charts.py
```

Las variables `ECO2026_PROCESSED_ROOT` y `ECO2026_SHARED_ROOT` permiten indicar
las carpetas de datos procesados y fuentes compartidas en otro entorno.
