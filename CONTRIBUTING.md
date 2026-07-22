# Colaboracion en RAIZ

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

Se prefieren commits pequenos y archivos seleccionados explicitamente:

```bash
git add ruta/del/archivo
git commit -m "Describe el cambio"
```

Antes del Pull Request se incorporan cambios recientes de `dev`. Para un equipo
pequeno con notebooks, `merge` evita reescribir historial compartido:

```bash
git switch dev
git pull
git switch feature/mi-cambio
git merge dev
git push -u origin feature/mi-cambio
```

El Pull Request se abre hacia `dev`. La promocion de `dev` a `main` se realiza
cuando el equipo considera estable la integracion.

## Notebooks y Drive

- No versionar datos grandes, credenciales ni rutas personales.
- Dejar banderas de ejecucion peligrosa en `False` antes de guardar.
- Evitar que dos personas editen el mismo notebook o escriban la misma particion.
- No usar outputs guardados como unica evidencia; conservar manifiestos y reportes.
- Ejecutar primero con un subconjunto y verificar entradas y salidas.
- Los crudos de Drive son inmutables; toda limpieza crea una capa nueva.

## Documentacion

- Actualizar `docs/project_status.md` cuando cambie alcance o estado.
- Actualizar `docs/data_artifacts.md` cuando cambie una salida.
- Guardar procedimientos reproducibles en `docs/` y conversaciones en
  `local_docs/`.
- Marcar como historica una recomendacion vencida o retirarla despues de fusionar
  su conocimiento vigente.
