# Candidatos de variables climáticas para el MVP

**Fecha de verificación:** 11 de julio de 2026

## Objetivo

Identificar variables que puedan cruzarse con EVA 2019–2025 para Boyacá y
Cundinamarca sin ampliar innecesariamente el alcance. La prioridad no es reunir
muchas fuentes, sino escoger una familia climática agronómicamente explicable y
procesable dentro del tiempo disponible.

## Recomendación ejecutiva

Las familias que vale la pena comparar son:

1. Precipitación.
2. Temperatura: media, mínima y máxima.
3. Humedad relativa.

Radiación solar sería una cuarta candidata útil si se adopta NASA POWER. Presión
atmosférica y viento pueden conservarse como secundarios, pero no deberían ser la
primera variable explicativa del rendimiento. No se encontró en datos.gov.co una
serie nacional operativa de humedad del suelo o radiación solar comparable con
las fuentes IDEAM por estación.

Con dos días disponibles, la alternativa más práctica es evaluar **NASA POWER**
como fuente climática unificada y conservar IDEAM/Socrata para contraste,
trazabilidad o trabajo futuro.

## Fuentes IDEAM en datos.gov.co

Todas las fuentes de esta tabla pertenecen a la Oficina de Informática del IDEAM,
tienen 12 columnas y presentan observaciones por estación.

| Variable | ID | Inicio cacheado | Último registro verificado en Boyacá y Cundinamarca | Prioridad |
|---|---|---|---|---|
| Precipitación | `s54a-sgyg` | 2003 | Julio de 2026 | Alta, pero muy pesada |
| Temperatura ambiente | `sbwg-7ju4` | 2001 | Julio de 2026 | Alta |
| Temperatura mínima | `afdg-3zpb` | 2001 | Julio de 2026 | Alta si el cultivo es sensible a frío o heladas |
| Temperatura máxima | `ccvq-rp9s` | 2001 | Julio de 2026 | Alta si el cultivo es sensible a calor |
| Humedad del aire | `uext-mhny` | 2001 | Julio de 2026 | Media-alta |
| Velocidad del viento | `sgfv-3yp8` | 2001 | Julio de 2026 | Media-baja |
| Presión atmosférica | `62tk-nxj5` | 2001 | Julio de 2026 | Baja como variable única |

URLs listas para el perfilador:

```text
https://www.datos.gov.co/resource/s54a-sgyg.json
https://www.datos.gov.co/resource/sbwg-7ju4.json
https://www.datos.gov.co/resource/afdg-3zpb.json
https://www.datos.gov.co/resource/ccvq-rp9s.json
https://www.datos.gov.co/resource/uext-mhny.json
https://www.datos.gov.co/resource/sgfv-3yp8.json
https://www.datos.gov.co/resource/62tk-nxj5.json
```

### Humedad relativa

- [Página oficial de Humedad del Aire](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Humedad-del-Aire/uext-mhny)
- Variable: humedad relativa del aire a dos metros.
- Unidad publicada: porcentaje.
- Frecuencia descrita: horaria, aunque la frecuencia real debe auditarse por
  estación.
- Utilidad: representa estrés atmosférico y condiciones favorables para algunas
  enfermedades.
- Riesgo: es una relación más indirecta con rendimiento que agua o temperatura y
  la fuente sigue siendo subdiaria y voluminosa.

### Temperatura mínima y máxima

- [Temperatura máxima del aire](https://www.datos.gov.co/d/ccvq-rp9s)
- [Temperatura mínima del aire](https://www.datos.gov.co/d/afdg-3zpb)
- [Temperatura ambiente del aire](https://www.datos.gov.co/d/sbwg-7ju4)

Las tres pueden tratarse como una sola **familia de temperatura**, no como tres
variables conceptuales independientes. Permiten construir:

- Temperatura media del periodo.
- Promedio de máximas y mínimas.
- Días fríos o calientes respecto a un umbral agronómico.
- Amplitud térmica.
- Grados-día, si se conoce una temperatura base defendible para el cultivo.

Para papa, las mínimas y máximas pueden tener más interpretación que una media
aislada, debido al riesgo de frío, heladas y estrés térmico.

### Viento y presión

Ambas fuentes tienen registros actuales en los dos departamentos, pero no se
recomiendan como primera elección:

- El viento interviene en evapotranspiración y daño físico, pero su efecto sobre
  rendimiento depende de otras variables.
- La presión atmosférica es principalmente una señal meteorológica indirecta y
  está muy asociada con altitud; por sí sola ofrece una historia agronómica débil.

## Normales climatológicas

- [Normales Climatológicas de Colombia](https://www.datos.gov.co/Ambiente-y-Desarrollo-Sostenible/Normales-Climatol-gicas-de-Colombia/nsz2-kzcq)
- ID: `nsz2-kzcq`.
- Periodos: 1961–1990 y 1991–2020.
- Incluye precipitación, temperatura, brillo solar, humedad y evaporación.

Es un dataset valioso como línea base climática o contexto territorial, pero no
es una serie 2019–2025. Al ser prácticamente estático, no explica la variación de
rendimiento entre años del MVP.

## Alternativa recomendada: NASA POWER

- [Documentación oficial Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [Documentación oficial Monthly API](https://power.larc.nasa.gov/docs/services/api/temporal/monthly/)

NASA POWER entrega datos solares y meteorológicos listos para análisis mediante
coordenadas. La API diaria ofrece datos desde 1981 hasta casi tiempo real y
permite solicitar hasta 20 parámetros para un punto.

Parámetros útiles para RAIZ:

| Código | Variable | Unidad mensual verificada |
|---|---|---|
| `PRECTOTCORR` | Precipitación corregida | mm/día |
| `T2M` | Temperatura a 2 m | °C |
| `T2M_MIN` | Temperatura mínima a 2 m | °C |
| `T2M_MAX` | Temperatura máxima a 2 m | °C |
| `RH2M` | Humedad relativa a 2 m | % |
| `ALLSKY_SFC_SW_DWN` | Radiación solar de onda corta en superficie | MJ/m²/día |
| `WS2M` | Velocidad del viento a 2 m | m/s |

### Prueba realizada

Una consulta mensual para una coordenada de Tunja, con los siete parámetros y
el periodo 2019–2025:

- Respondió correctamente.
- Pesó aproximadamente 10 KB.
- Tardó menos de cinco segundos.
- Devolvió elevación aproximada y series mensuales para todos los parámetros.

Esto contrasta con las centenas de miles de observaciones subdiarias de un solo
mes IDEAM.

### Ventajas

- Una sola API para todas las variables candidatas.
- Datos diarios o mensuales ya organizados.
- Periodo compatible con EVA 2019–2025.
- Sin paginación por millones de observaciones.
- Evita resolver sensores y frecuencias diferentes por estación.

### Cautelas

- No son mediciones directas de una estación municipal; son productos de rejilla
  derivados de fuentes como MERRA-2 y CERES.
- La documentación advierte que la rejilla global es aproximadamente de 0,5° y
  que no deben repetirse solicitudes para la misma celda.
- En Boyacá y Cundinamarca, la topografía montañosa puede generar diferencias
  importantes dentro de una celda.
- Varios municipios pueden compartir el mismo valor climático de rejilla.
- Debe documentarse como aproximación espacial y no presentarse como observación
  exacta en cada cultivo.

Para evitar solicitudes repetidas, conviene descargar por región o identificar
celdas únicas y luego asignar cada municipio a la celda más cercana.

## Qué escoger para el MVP

### Si se escoge papa

Comparar primero:

1. Familia de temperatura: `T2M`, `T2M_MIN`, `T2M_MAX`.
2. Precipitación: `PRECTOTCORR`.
3. Humedad relativa: `RH2M`, solo si mejora el baseline y puede explicarse.

### Si se escoge maíz

Comparar primero:

1. Precipitación.
2. Familia de temperatura.
3. Radiación solar como candidata secundaria.

## Ruta sugerida para los dos días restantes

1. Usar EVA UPRA 2019–2025 para seleccionar papa o maíz.
2. Probar NASA POWER mensual o diario para el mismo periodo.
3. Construir agregados por semestre o año, según `Periodo` y ciclo del cultivo.
4. Entrenar modelos mínimos por familia climática y compararlos contra el mismo
   baseline.
5. Escoger una sola familia para la narrativa final.
6. Conservar las APIs IDEAM como fuente oficial nacional y como trabajo de
   validación futura, sin descargar ahora todo el histórico subdiario.

## Fuentes que no se priorizan

- Presión atmosférica como único predictor.
- Dirección del viento.
- Calidad del aire.
- Normales climatológicas como predictor temporal.
- Datasets locales de una sola estación o un solo municipio.
- Humedad del suelo sin cobertura nacional y temporal comprobada.
- Rasters o nuevas capas geoespaciales que requieran una infraestructura distinta.
