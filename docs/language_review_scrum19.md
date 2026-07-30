# Revisión de lenguaje documental — SCRUM-19

**Actualizado:** 30 de julio de 2026

**Estado:** vigente

**Alcance:** documentos de entrada, estado y presentación de resultados

## Objetivo

Alinear el lenguaje de la documentación con el estado verificable de rAIz y
evitar que una descripción aspiracional se interprete como una capacidad ya
implementada.

## Hallazgos

1. El README indicaba que el proyecto seguía en descubrimiento, aunque ya existen
   flujos ejecutados, un conjunto de datos definitivo y pronósticos para 2026.
2. La descripción atribuía al producto una evaluación general de riesgos
   climáticos y una integración de suelos que no forman parte del modelo
   vigente.
3. Los documentos principales alternaban palabras sin tilde y anglicismos sin
   explicación.
4. Las métricas del modelo aparecían mediante siglas antes de que una persona no
   especialista pudiera interpretarlas.
5. Era necesario diferenciar resultados observados, climatología utilizada para
   completar 2026-B y pronósticos aún no contrastados con EVA 2026.

## Acciones aplicadas

- Se reescribió el README con el alcance vigente, los resultados del análisis,
  las métricas explicadas, el pronóstico 2026 y sus limitaciones.
- Se corrigió el lenguaje de los puntos de entrada
  `README.md`, `CONTRIBUTING.md`, `docs/README.md` y `docs/project_status.md`.
- Se incorporaron reglas mínimas de redacción para futuras contribuciones.
- Se conservaron los nombres técnicos de archivos, columnas, modelos y
  artefactos cuando traducirlos pudiera romper la trazabilidad.
- No se modificaron documentos históricos archivados, porque deben preservar el
  contexto de la decisión original.

## Criterios editoriales vigentes

- Definir siglas y métricas en su primera aparición.
- Diferenciar **implementado**, **ejecutado**, **auditado** y **aprobado**.
- Incluir unidad, período, fecha de corte y fuente al presentar cifras.
- Mostrar limitaciones y segmentos débiles junto al resultado principal.
- Usar **pronóstico** para una estimación futura y **predicción** para el
  concepto o la familia de métodos.
- No presentar como capacidad productiva una exploración o un notebook aislado.
