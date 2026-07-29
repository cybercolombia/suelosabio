# Auditoria geografica de precipitacion 2024-2025

**Fecha de ejecucion:** 24 de julio de 2026
**Fuente climatica:** `s54a-sgyg`
**Contrato geografico:** `climate_station_geography_v1`
**Estado:** `COMPLETA_SIN_POLIGONOS`
**Commit de ejecucion:** `04b1bd6af7b713f9e886b4efb66d39a28e5ef48b`

## Entrada y productos

La corrida leyo las 48 particiones y 53.128 filas estacion-dia del cierre
`cierre_precipitacion_2024_2025_v2`. Escribio en la carpeta personal
`eco2026_processed/geografia_curada`, sin modificar `eco2026`.

Productos persistidos:

- Catalogo de 126 estaciones climaticas.
- 126 candidatos estacion-municipio.
- 15 estaciones para revision.
- Catalogo de 239 municipios objetivo.
- Resumen por departamento.
- Mapa HTML, reporte y manifiesto.

## Reconciliacion

| Control | Resultado |
|---|---:|
| Estaciones climaticas | 126 |
| Estaciones unicas | 126 |
| Duplicados por codigo | 0 |
| Estaciones encontradas en IDEAM | 126 |
| Coordenadas IDEAM faltantes | 0 |
| Candidatos sin alertas, verdes | 111 |
| Candidatos para revision, naranjas | 15 |
| DIVIPOLA resuelta por nombre | 122 |
| Asignaciones canonicas | 0 |

Boyaca contiene 67 estaciones, cuatro en revision. Cundinamarca contiene 59,
once en revision.

## Motivos de revision

Los motivos no son excluyentes:

| Motivo | Estaciones | Interpretacion |
|---|---:|---|
| `COORDENADA_DIFIERE` | 9 | Diferencia mayor a 0,001 grados entre clima e IDEAM |
| `DIVIPOLA_NO_RESUELTA` | 4 | Variante o error nominal sin alias aprobado |
| `MUNICIPIO_MULTIPLE` | 2 | La fuente climatica reporto mas de un municipio |
| `DEPARTAMENTO_DISCREPANTE` | 1 | La descarga y el catalogo IDEAM difieren |
| `FUERA_ALCANCE_GEOGRAFICO` | 1 | Estacion IDEAM ubicada en Bogota |

Las nueve diferencias de coordenadas representan aproximadamente entre 0,14 km
y 2,06 km. No se corrigen automaticamente: una diferencia puede ser una
actualizacion de catalogo, redondeo, desplazamiento de sensor o error.

Los cuatro nombres no resueltos son candidatos claros para una tabla de alias,
pero requieren aprobacion explicita:

- `Villa De Leiva` frente a `VILLA DE LEYVA`, dos estaciones.
- `Pisva` frente a `PISBA`, una estacion.
- `Ubate` frente a `VILLA DE SAN DIEGO DE UBATE`, una estacion.

Los dos municipios multiples son:

- `0023067060`: `LA PENA | NIMAIMA`; IDEAM indica La Pena.
- `0035027100`: `CHIPAQUE | UNE`; IDEAM indica Chipaque.

La estacion `2120500204`, IDEAM Puente Aranda, pertenece a Bogota aunque fue
descargada dentro de Cundinamarca. Debe excluirse del alcance o tratarse mediante
una excepcion documentada.

## Decision

La auditoria tabular y el mapa se aprueban. La tabla de candidatos sirve para
revision, pero no para agregar clima por municipio. El paso 07 permanece
bloqueado hasta conseguir poligonos municipales completos, ejecutar
punto-en-poligono y publicar una asignacion canonica versionada.

Mientras se resuelve esta compuerta, precipitacion puede pausarse y el equipo
puede avanzar en paralelo con los pilotos diarios de temperatura.
