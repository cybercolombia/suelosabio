# Auditoria de precipitacion municipal diaria

**Actualizado:** 29 de julio de 2026
**Estado:** implementada y prevalidada localmente; corrida oficial en Colab pendiente
**Alcance:** Boyaca y Cundinamarca, 2024-2025

`07_ClimateMunicipalAudit.ipynb` audita la salida de
`07_ClimateMunicipalAggregator.ipynb` sin recalcularla, modificarla ni imputar
ausencias. La logica de precipitacion vive en
`PrecipitationMunicipalAudit.py`; otras variables deben definir su propio
contrato de auditoria municipal.

## Entrada

```text
eco2026_processed/
  clima_municipal/
    variable=precipitacion/
      fuente=s54a-sgyg/
        agregacion=precipitacion_municipio_dia_2024_2025_v1/
```

La entrada esperada tiene manifiesto `COMPLETA`, contrato
`precipitacion_municipio_dia_v1`, 48 particiones y 174.709 filas.

## Preguntas

La auditoria responde:

1. Cuantos dias validos tiene cada municipio frente al calendario y frente a
   su ventana con estaciones esperadas.
2. Cual es la brecha consecutiva maxima sin valor.
3. Donde se concentran los 92 municipio-dias con cobertura inferior a 50 %.
4. Cuanto difieren media y mediana en los 5.096 dias multiestacion.
5. Cuanto cambia la clasificacion de dia lluvioso para umbrales diagnosticos de
   0,1; 1; 5; 10 y 20 mm.
6. Cuanto cambian los acumulados anuales al usar media o mediana sobre
   exactamente los mismos dias validos.

Los umbrales son pruebas de sensibilidad, no decisiones agronomicas.

## Salida

```text
eco2026_processed/
  auditorias_clima_municipal/
    variable=precipitacion/
      fuente=s54a-sgyg/
        auditoria=cierre_precipitacion_municipal_2024_2025_v1/
          cobertura_municipios.parquet
          cobertura_periodos.parquet
          cobertura_insuficiente.parquet
          multiestacion_dias.parquet
          resumen_multiestacion.parquet
          sensibilidad_media_mediana_anual.parquet
          sensibilidad_umbrales_lluvia.parquet
          cobertura_temporal_municipios.html
          sensibilidad_media_mediana.html
          AuditoriaMunicipal_precipitacion_2024_2025.md
          manifest.json
```

`cobertura_periodos.parquet` resume mes, semestre y ano. Conserva cobertura
sobre calendario, cobertura sobre dias con estacion esperada y brechas
consecutivas; no extrapola acumulados.

## Prevalidacion local

La ejecucion sobre la copia oficial confirmo:

- 84 municipios con estacion canonica y 155 sin ella.
- 25.856 de 37.651 municipio-dias esperados validos: 68,67 %.
- 92 dias con cobertura insuficiente, concentrados en Guasca (34), Aquitania
  (25), Chiscas (23) y Puerto Salgar (10).
- 5.096 dias multiestacion en 17 municipios.
- Diferencia absoluta media-mediana de 0 mm en la mediana de los casos, 1,457
  mm en el percentil 95 y 73,113 mm como maximo.
- Para el umbral diagnostico de 1 mm, media y mediana clasifican de forma
  distinta 184 dias, 3,61 % de los dias multiestacion.

La sensibilidad anual es material en algunos municipios. En 2025, sobre los
mismos dias validos, la suma de medias supera la suma de medianas en
aproximadamente 244 % para Puerto Salgar y 103 % para Aquitania. Esto no prueba
que la mediana sea correcta, pero impide aprobar la regla sin revisar la
dispersion y las estaciones contribuyentes.

## Ejecucion segura

1. Abrir `07_ClimateMunicipalAudit.ipynb` desde `feature/SCRUM-14`.
2. Ejecutar con `EJECUTAR_AUDITORIA_MUNICIPAL=False`.
3. Confirmar entrada `COMPLETA`, version municipal v1, 48 particiones y 174.709
   filas en el manifiesto.
4. Mantener `GUARDAR_RESULTADOS=True` y
   `SOBRESCRIBIR_AUDITORIA=False`.
5. Cambiar solo `EJECUTAR_AUDITORIA_MUNICIPAL=True`.
6. Ejecutar nuevamente desde la configuracion hasta el final.
7. Volver a dejar la bandera en `False` antes de guardar el notebook.

## Compuerta

El estado esperado de esta auditoria es
`COMPLETA_CON_REVISION_PENDIENTE`. Antes del paso 08 se debe:

- revisar los dias y estaciones de Aquitania y Puerto Salgar con mayor
  dispersion;
- decidir si la mediana v1 se mantiene o requiere una regla adicional;
- definir cobertura minima por mes, semestre o ciclo agricola;
- cruzar la cobertura con los municipios y cultivos presentes en EVA;
- mantener `NaN` donde no exista evidencia suficiente.
