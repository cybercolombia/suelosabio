# CropForecasting

Esta carpeta concentra **todo** el trabajo predictivo de rendimiento agrícola:
construcción del dataset, escenarios climáticos, backtesting, modelos, notebooks,
pruebas y documentación.

## Objetivo

Pronosticar el rendimiento de papa en los semestres A y B de 2026 para los diez
municipios de mayor área sembrada reciente en Boyacá y los diez de Cundinamarca.
La selección usa exclusivamente 2024–2025.

## Estrategia

1. Lee EVA UPRA 2019–2025 y recalcula el rendimiento agregado.
2. Descarga NASA POWER por celda climática, sin repetir solicitudes por municipio.
3. Construye indicadores por municipio y semestre.
4. Usa observaciones completas para 2026-A y, para 2026-B, observaciones hasta
   el 30 de julio de 2026 más climatología histórica para el resto del semestre.
5. Evalúa modelos con backtesting expansivo 2021–2025.
6. Selecciona por MAE promedio de 2024–2025, entrena con 2019–2025 y pronostica
   las 40 combinaciones municipio-semestre de 2026.

Producción y área cosechada nunca se usan como predictores porque definen
directamente el rendimiento.

## Ejecución

Desde la raíz del repositorio:

```bash
.venv/bin/python -m notebooks.CropForecasting.run_pipeline
```

En Colab:

```bash
python -m notebooks.CropForecasting.run_pipeline --colab
```

Los datos y modelos se guardan bajo
`eco2026_processed/crop_forecasting/`; no se versionan archivos pesados.
