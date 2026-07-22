# Alerta transversal de cobertura: febrero de 2025

**Actualizado:** 22 de julio de 2026  
**Estado:** alerta confirmada en varias fuentes; causa pendiente  
**Alcance:** Boyaca y Cundinamarca

Febrero de 2025 presenta una reduccion abrupta de registros en varias fuentes
climaticas de IDEAM publicadas en datos.gov.co. No debe interpretarse como un
fenomeno meteorologico: el numero de observaciones refleja disponibilidad y
frecuencia de sensores, no la magnitud fisica de lluvia, temperatura o humedad.

## Evidencia de filas crudas

| Variable | Departamento | Enero | Febrero | Marzo | Febrero / enero |
|---|---|---:|---:|---:|---:|
| Precipitacion | Boyaca | 356.908 | 34.862 | 136.764 | 9,8 % |
| Precipitacion | Cundinamarca | 350.584 | 37.716 | 142.234 | 10,8 % |
| Temperatura ambiente | Boyaca | 71.112 | 10.630 | 33.396 | 14,9 % |
| Temperatura ambiente | Cundinamarca | 79.582 | 11.525 | 36.982 | 14,5 % |
| Temperatura minima | Boyaca | 33.022 | 2.829 | 11.597 | 8,6 % |
| Temperatura minima | Cundinamarca | 44.217 | 4.216 | 17.823 | 9,5 % |
| Temperatura maxima | Boyaca | 32.228 | 2.775 | 11.330 | 8,6 % |
| Temperatura maxima | Cundinamarca | 44.568 | 4.238 | 17.912 | 9,5 % |
| Humedad | Cundinamarca | 79.454 | 11.524 | 36.815 | 14,5 % |

## Lo demostrado y lo pendiente

Para precipitacion, 03_01 demostro que los dos departamentos carecen por
completo de observaciones entre el 5 y el 25 de febrero. Una consulta directa a
Socrata confirmo que el hueco ya existe en la fuente y no fue creado por la
descarga local.

Para temperatura y humedad esta tabla confirma una caida de volumen muy similar,
pero las auditorias disponibles no han construido todavia un calendario diario
completo para demostrar que coincidan exactamente los mismos 21 dias. Esa es una
hipotesis fuerte que debe verificarse con 03 y 03_01.

Presion atmosferica y velocidad del viento no tienen auditorias suficientes para
afirmar o descartar el mismo patron.

## Consecuencias para el pipeline

- Febrero debe formar parte obligatoria de los pilotos de cada variable.
- Los dias ausentes se conservan como `NaN`, nunca como cero.
- No se imputan observaciones subdiarias para ocultar el hueco.
- Los indicadores mensuales o semestrales deben incluir cobertura y brecha
  maxima; un valor parcial no se presenta como periodo completo.
- Antes de modelar se debe evaluar si la ausencia es sistemica entre variables.
  Si lo es, una imputacion conjunta puede introducir falsa confianza y fuga.
- La causa puede estar en adquisicion, publicacion o disponibilidad de una red
  comun de estaciones; los conteos por si solos no permiten escoger una causa.

