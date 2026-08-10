# Fitlosophy

Sistema personal de entrenamiento adaptativo orientado a combinar acondicionamiento físico, BJJ, pérdida de grasa, fuerza y prevención de lesiones.

El proyecto evita calendarios rígidos. La sesión del día se decide a partir de:

- Estado de recuperación.
- Carga acumulada reciente.
- Existencia o no de una sesión de BJJ.
- Estado de la zona lumbar y articulaciones.
- Objetivo físico prioritario del día.

## Objetivo técnico

La información del sistema se mantiene inicialmente en Markdown y YAML para que pueda consumirse desde una futura aplicación en React o Svelte sin acoplar todavía el diseño funcional a un framework concreto.

## Estrategia de producto

La aplicación no se construirá hasta que el modelo funcional pueda validarse manualmente con casos reales, reglas y pseudocódigo.

El roadmap completo se encuentra en [`docs/10-roadmap-del-producto.md`](docs/10-roadmap-del-producto.md).

### Fases del producto

0. Contexto y visión.
1. Modelo de dominio.
2. Biblioteca de conocimiento.
3. Modelo de carga e inferencia.
4. Motor de decisión.
5. Generador de sesiones.
6. Casos de uso y validación manual.
7. Diseño del MVP.
8. Construcción del MVP.
9. Uso personal y calibración.
10. Producto personal completo.
11. Integraciones opcionales.
12. Adaptación avanzada.

La puerta de entrada al desarrollo de la aplicación se abre cuando las **fases 0 a 6** están suficientemente cerradas.

El próximo hito es disponer de un **modelo funcional validable**: generar y justificar sesiones para los escenarios principales usando únicamente documentación, biblioteca, historial de ejemplo y pseudocódigo.

## Estructura

```text
fitlosophy/
├── README.md
├── CHANGELOG.md
├── docs/
│   ├── 00-contexto-completo-del-programa.md
│   ├── 01-perfil-y-objetivos.md
│   ├── 02-filosofia-del-sistema.md
│   ├── 03-motor-de-decision.md
│   ├── 04-gestion-de-carga.md
│   ├── 05-biblioteca-de-ejercicios.md
│   ├── 06-plantillas-de-sesion.md
│   ├── 07-progresion.md
│   ├── 08-registro-y-evaluacion.md
│   ├── 09-fuentes-de-datos-e-inferencias.md
│   ├── 10-roadmap-del-producto.md
│   ├── 11-glosario-y-modelo-de-dominio.md
│   ├── 12-modelo-de-carga-e-inferencia.md
│   ├── 13-casos-de-uso-y-validacion.md
│   └── 14-diseno-del-mvp.md
├── app/
│   ├── backend/             # Motor en Python (fitlosophy) + API FastAPI/SQLite (fitlosophy_api) + tests pytest
│   └── frontend/            # MVP: Svelte 5 + Tailwind 4, 6 pantallas + login (Vite)
└── data/
    ├── perfil.yaml
    └── ejercicios.yaml
```

## Puesta en marcha y despliegue

La aplicación corre como servicio systemd del usuario en el propio servidor, que
es a la vez entorno de desarrollo y de producción, y se publica por un túnel de
Cloudflare. Un único proceso sirve la API y el frontend compilado.

**Desplegar una actualización** (recompila, reinicia y verifica):

```bash
./scripts/desplegar.sh
```

Recompilar no es opcional: el backend sirve `app/frontend/dist`, así que un
cambio en Svelte que no se compile no llega a la URL aunque reinicies.

**Primera instalación**, resumida (detalle completo en
[`app/backend/README.md`](app/backend/README.md)):

1. Dependencias: `cd app/backend && python3 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"`, y `cd app/frontend && npm ci`.
2. Configuración: `cp app/backend/.env.example app/backend/.env` y rellenarlo.
3. Usuario único: `./.venv/bin/python scripts/init_db.py` (una sola vez; no hay registro).
4. Servicio: `systemctl --user enable --now fitlosophy` y `sudo loginctl enable-linger $USER`.
5. Cortafuegos: reglas de ufw para la LAN y para `docker0`, sin las cuales el túnel no alcanza el host.

Comandos útiles: `systemctl --user status fitlosophy`, `journalctl --user -u fitlosophy -f`.

## Estado actual

**Las fases 0 a 8 del roadmap están cerradas** (`docs/10`): contexto y visión, modelo de dominio (`docs/11`), biblioteca (`data/ejercicios.yaml`, `docs/05`), modelo de carga (`docs/12`), motor de decisión (`docs/03`), generador de sesiones (`docs/06`), validación con casos de uso (`docs/13`), diseño del MVP (`docs/14`) y su construcción.

La aplicación está **desplegada y en uso**: un único proceso sirve la API y el frontend compilado tras un túnel de Cloudflare. Los 9 criterios de aceptación de `docs/14` están cubiertos y la suite tiene 98 tests en verde (`cd app/backend && ./.venv/bin/python -m pytest`). Stack: Svelte 5 + Tailwind 4 (frontend responsive), FastAPI + SQLite (backend), systemd + Cloudflare Tunnel (despliegue).

**La Fase 9 (uso personal y calibración) está en curso desde el 10 de agosto de 2026.** Es la que no se programa: todos los valores numéricos de `docs/12` —puntos por nivel de coste, multiplicadores de dosis, ventanas de decaimiento— siguen siendo provisionales y se calibran con historial real. Los datos necesarios se persisten con el uso normal y se exportan con `GET /api/export`.
