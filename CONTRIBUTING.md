# Colaboración en RAIZ

## Antes de trabajar

1. Leer `docs/README.md` y `docs/project_status.md`.
2. Confirmar la etapa, entrada y salida en `docs/project_roadmap.md` y
   `docs/data_artifacts.md`.
3. Partir de la rama `dev` actualizada.

## Flujo Git

```bash
git switch dev
git pull
git switch -c feature/mi-cambio
```

Se prefieren commits pequeños y archivos seleccionados explícitamente:

```bash
git add ruta/del/archivo
git commit -m "Describe el cambio"
```

Antes de la solicitud de integración (pull request) se incorporan cambios
recientes de `dev`. Para un equipo pequeño con notebooks, `merge` evita
reescribir el historial compartido:

```bash
git switch dev
git pull
git switch feature/mi-cambio
git merge dev
git push -u origin feature/mi-cambio
```

La solicitud de integración se abre hacia `dev`. La promoción de `dev` a `main`
se realiza cuando el equipo considera estable la integración.

## Notebooks y Drive

- No versionar datos grandes, credenciales ni rutas personales.
- Dejar banderas de ejecución peligrosa en `False` antes de guardar.
- Evitar que dos personas editen el mismo notebook o escriban la misma partición.
- No usar salidas guardadas como única evidencia; conservar manifiestos y
  reportes.
- Ejecutar primero con un subconjunto y verificar entradas y salidas.
- Los crudos de Drive son inmutables; toda limpieza crea una capa nueva.

Antes de confirmar cambios, elimine salidas, contadores de ejecución y estado de
widgets:

```bash
python3 scripts/notebook_outputs.py --fix
python3 scripts/notebook_outputs.py
```

El hook local puede instalarse con `pre-commit install`; limpia automáticamente
los notebooks modificados. La integración continua repite la limpieza en una
copia del repositorio y falla si detecta una diferencia, para impedir que las
salidas guardadas entren en `dev` o `main`. El tamaño o número de líneas de un
archivo `.ipynb` no sustituye esta validación estructural.

## Documentación

- Actualizar `docs/project_status.md` cuando cambie alcance o estado.
- Actualizar `docs/data_artifacts.md` cuando cambie una salida.
- Guardar procedimientos reproducibles en `docs/` y conversaciones en
  `local_docs/`.
- Marcar como histórica una recomendación vencida o retirarla después de fusionar
  su conocimiento vigente.

## Lenguaje documental

- Escribir en español claro y conservar tildes, signos y nombres oficiales.
- Definir una sigla o métrica la primera vez que aparezca.
- Distinguir entre un proceso implementado, uno ejecutado y uno aprobado.
- Usar **pronóstico** para resultados futuros y **predicción** como concepto
  general del modelo.
- Indicar fecha de corte, fuente y unidad junto a cada resultado cuantitativo.
- Presentar las limitaciones junto a los resultados, no como una nota aislada.
