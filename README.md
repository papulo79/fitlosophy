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

## Estrategia de producto

La aplicación no se construirá hasta que el modelo funcional pueda validarse manualmente con casos reales y pseudocódigo.

El roadmap completo se encuentra en [`docs/10-roadmap-del-producto.md`](docs/10-roadmap-del-producto.md).

Fases principales:

1. Contexto y visión.
2. Modelo de dominio.
3. Biblioteca de conocimiento.
4. Modelo de carga e inferencia.
5. Motor de decisión.
6. Generador de sesiones.
7. Validación manual mediante casos de uso.
8. Definición del MVP.
9. Construcción de la aplicación.
10. Calibración con uso real.
11. Producto personal completo.
12. Integraciones y adaptación avanzada.

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
│   └── 10-roadmap-del-producto.md
└── data/
    ├── perfil.yaml
    └── ejercicios.yaml
```

## Estado actual

El proyecto se encuentra entre las fases de **modelo de dominio**, **biblioteca de conocimiento** y diseño inicial del **motor de decisión**.

Todavía no se ha alcanzado la puerta de entrada al desarrollo de la aplicación. Antes deben cerrarse:

- el modelo de dominio;
- la biblioteca inicial;
- el modelo de carga;
- el cuestionario diario;
- las reglas del motor;
- las plantillas de sesión;
- la validación manual con casos de uso.
