# Pipeline de auditoría y curación EVA

**Actualizado:** 29 de julio de 2026  
**Estado:** implementado y ejecutado; revisión humana pendiente  
**Alcance:** Boyacá y Cundinamarca

## Propósito

El pipeline agrícola aplica las mismas garantías transversales del pipeline
climático —crudos inmutables, auditorías separadas, salidas versionadas,
reconciliación y compuertas explícitas— sin copiar su reducción diaria, porque
EVA ya se publica por municipio y período agrícola.

```text
01.2 descarga EVA
  -> eva_cruda
  -> 02.2 auditoría cruda
  -> 09 curación y target
  -> 09.2 auditoría curada
  -> paso 10 dataset maestro
```

## 02.2 Auditoría cruda

`02_2_CropYieldDataAudit.ipynb` es de solo lectura. Revisa:

- esquema y conversiones;
- cobertura por departamento, año, período y cultivo;
- códigos DANE y correspondencia municipio-departamento;
- períodos anuales y semestrales frente al ciclo del cultivo;
- nulos, negativos, área cosechada no positiva y cosecha mayor que siembra;
- llaves repetidas por desagregación, ciclo y estado físico;
- diferencia entre rendimiento publicado y `producción / área cosechada`.

Los hallazgos se escriben en `auditorias_agricultura/capa=eva_cruda`. Un estado
`COMPLETA_CON_REVISION_PENDIENTE` confirma que la auditoría terminó; no aprueba
automáticamente la consolidación.

## 09 Curación

`09_EvaCurator.ipynb` produce una fila por:

```text
codigo_municipio + anio + periodo + cultivo
```

Solo consolida filas con ciclo y estado físico compatibles. Las llaves con
taxonomías incompatibles se exportan a `exclusiones.parquet`; no se suman en
silencio. El target se recalcula como:

```text
rendimiento_t_ha = produccion_t / area_cosechada_ha
```

Producción y área cosechada permanecen para auditar el target, pero el
manifiesto las declara columnas no predictoras para evitar fuga. La salida marca
el cambio metodológico documentado desde 2022.

## 09.2 Auditoría curada

`09_2_EvaCuratedAudit.ipynb` valida unicidad, llaves nulas, medidas finitas,
reproducción exacta de la fórmula y cobertura territorial/temporal. Solo una
corrida revisada debe habilitar el paso 10.

## Agregado municipal para mapas

`CropMunicipalChangeRunner.py` materializa una fila por municipio, año, período
y cultivo sin mezclar períodos A, B y anuales. Conserva el área sembrada aunque
la cosecha sea cero; el rendimiento solo se calcula cuando hay área cosechada
positiva y siempre usa la razón entre producción total y área cosechada total.

La corrida `cultivo_municipio_periodo_v1` procesó 14.962 filas, produjo 13.692
targets y 9.377 comparaciones interanuales. Los 239 códigos municipales enlazan
con los 239 polígonos DIVIPOLA; 43 filas incompatibles entre ciclo y período se
conservaron como incidencias y no entraron al agregado. Los 1.159 targets con
múltiples desagregaciones están identificados para revisión taxonómica.

## Decisiones todavía pendientes

- Confirmar si la fuente final será el Excel UPRA 2019–2025 o la API Socrata
  2019–2024 usada por el descargador actual.
- Elegir uno o dos cultivos; `CULTIVOS_OBJETIVO=None` evita inferir esa decisión.
- Revisar manualmente taxonomías incompatibles y diferencias de rendimiento.
- Decidir si el análisis principal usa 2019–2025 o 2022–2025 por el quiebre
  metodológico.
