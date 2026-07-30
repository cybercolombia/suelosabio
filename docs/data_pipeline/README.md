# Documentación consolidada del ciclo de datos

**Actualizado:** 30 de julio de 2026
**Alcance:** Boyacá y Cundinamarca

Esta carpeta documenta la conversión de cada fuente en un producto analítico.
Los reportes de `docs/climate_audits/` conservan
la evidencia detallada de cada ejecución; no sustituyen estos contratos.

## Ruta de lectura

1. [Clima por variable](climate.md): descarga, auditoría, limpieza,
   homogeneización subdiaria-diaria, consolidación y agregado municipal.
2. [Cultivos](agriculture.md): auditoría EVA, normalización de períodos,
   agregado municipio × cultivo × período y cambios interanuales.
3. [Geografía](geography.md): catálogo de estaciones, polígonos DIVIPOLA,
   asignación punto-en-polígono y llaves de cruce.
4. [Pronóstico](forecast.md): dataset definitivo, validación temporal,
   comparación de métodos y pronóstico de papa 2026.
5. [Resumen para presentación](../presentation/RESULTADOS_PROCESO_DATOS_2026.md):
   resultados acompañados de gráficas y mapas reproducibles.

## Capas y granularidades

| Dominio | Entrada | Producto intermedio | Producto comparable |
|---|---|---|---|
| Clima IDEAM | Observación subdiaria por estación y sensor | Estación × sensor × día; estación × día | Municipio × día |
| Clima NASA POWER | Celda geográfica × día | Municipio × día | Municipio × semestre |
| Cultivos EVA | Registro publicado por municipio, cultivo y período | Registro curado compatible | Municipio × cultivo × período |
| Geografía | Estaciones y polígonos municipales | Asignación canónica estación-municipio | Código DANE como llave común |
| Pronóstico | Historia agrícola + clima por semestre + geografía | Una fila por municipio, papa, año y semestre | Rendimiento 2026A y 2026B |

La comparación no se consigue forzando todos los dominios a ser diarios. Se
conserva la frecuencia natural de cada fuente y solo se agregan los datos cuando
existe una regla científica explícita.

## Reglas transversales

- El dato crudo no se sobrescribe.
- Toda salida lleva versión, manifiesto y granularidad conocida.
- Los duplicados exactos pueden eliminarse con conteo; los conflictos de valor
  se aíslan y no se promedian silenciosamente.
- Una ausencia climática permanece ausente; no se convierte en cero.
- Producción y área cosechada sirven para auditar el rendimiento, pero no son
  predictores porque revelarían directamente la variable objetivo.
- Una ejecución completa significa que terminó técnicamente. La aprobación
  científica de cobertura o taxonomía se registra por separado.
