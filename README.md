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
│   └── backend/             # Motor en Python + tests (pytest)
└── data/
    ├── perfil.yaml
    └── ejercicios.yaml
```

## Estado actual

Las fases 0 a 6 del roadmap están cerradas en su primera versión: contexto y visión, modelo de dominio (`docs/11`), biblioteca (`data/ejercicios.yaml`, `docs/05`), modelo de carga (`docs/12`), motor de decisión (`docs/03`), generador de sesiones (`docs/06`) y validación manual con casos de uso (`docs/13`). Todos los valores numéricos son provisionales y se calibrarán con uso real.

El MVP está definido (`docs/14`): flujo de uso real, pantallas, marcado por ítem y criterios de aceptación.

La Fase 8 (construcción) está en curso: el motor de decisión y el generador de sesiones están implementados en Python (`app/backend/`, paquete `fitlosophy`) y la API REST con autenticación y persistencia SQLite está operativa (`fitlosophy_api`, ver `app/backend/README.md`). Los 10 casos de `docs/13` y el flujo completo del MVP son tests ejecutables (`cd app/backend && python3 -m pytest`). Stack: Svelte 5 + Tailwind 4 (frontend, responsive), FastAPI + SQLite (backend), despliegue con Cloudflare Tunnel. Siguiente paso: el frontend con las 6 pantallas del MVP.
