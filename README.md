# Fitlosophy

Sistema personal de entrenamiento adaptativo orientado a combinar acondicionamiento físico, BJJ, pérdida de grasa, fuerza y prevención de lesiones.

El proyecto evita calendarios rígidos. La sesión del día se decide a partir de varios inputs:

- Estado de recuperación.
- Carga acumulada en las últimas 48-72 horas.
- Existencia o no de una sesión de BJJ.
- Estado de la zona lumbar y articulaciones.
- Objetivo físico prioritario del día.

## Objetivo técnico

La información del sistema se mantiene en Markdown y YAML para que pueda consumirse desde una futura aplicación en React o Svelte sin acoplarla todavía a un framework concreto.

## Estructura

```text
fitlosophy/
├── README.md
├── CHANGELOG.md
├── docs/
│   ├── 01-perfil-y-objetivos.md
│   ├── 02-filosofia-del-sistema.md
│   ├── 03-motor-de-decision.md
│   ├── 04-gestion-de-carga.md
│   ├── 05-biblioteca-de-ejercicios.md
│   ├── 06-plantillas-de-sesion.md
│   ├── 07-progresion.md
│   └── 08-registro-y-evaluacion.md
└── data/
    ├── perfil.yaml
    └── ejercicios.yaml
```

## Estado

Versión inicial del modelo de dominio y la documentación. La aplicación web se añadirá en una fase posterior.
