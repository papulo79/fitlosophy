# AGENTS.md — Fitlosophy

Guía para agentes de IA que trabajen en este repositorio.

## Descripción del proyecto

Fitlosophy es un **sistema personal de entrenamiento adaptativo** (no una aplicación, todavía). Combina acondicionamiento físico, BJJ (jiu-jitsu brasileño), pérdida de grasa, fuerza y prevención de lesiones para un único atleta. En lugar de calendarios rígidos, la sesión del día se decide a partir de inputs como la recuperación, la carga de las últimas 48–72 h, la existencia de una sesión de BJJ y el estado de la zona lumbar.

El sistema vive íntegramente en **Markdown (documentación del modelo de dominio) y YAML (datos)**, mantenidos de forma deliberadamente independiente de cualquier framework para que una futura aplicación web (React o Svelte) pueda consumirlos. **No hay código ejecutable, ni tests, ni build** en el estado actual (v0.1.0).

## Estructura del repositorio

```text
fitlosophy/
├── README.md            # Visión general y estado del proyecto
├── CHANGELOG.md         # Historial de versiones (formato simple por versión)
├── AGENTS.md            # Este archivo
├── docs/                # Documentación del modelo de dominio, numerada en orden de lectura
│   ├── 00-contexto-completo-del-programa.md  # Documento agregador: todo el contexto funcional, personal y conceptual en un solo archivo (pseudocódigo y reglas, sin implementación)
│   ├── 01-perfil-y-objetivos.md      # Quién es el atleta y qué persigue
│   ├── 02-filosofia-del-sistema.md   # Principios y los tres tipos de día
│   ├── 03-motor-de-decision.md       # Inputs, orden de decisión y árbol de la sesión diaria
│   ├── 04-gestion-de-carga.md        # Semáforo de recuperación (verde/amarillo/rojo) y reglas de carga
│   ├── 05-biblioteca-de-ejercicios.md# Categorías, etiquetas y criterio lumbar de los ejercicios
│   ├── 06-plantillas-de-sesion.md    # Generador: plantillas A-D, composición, dosificación, sustitución, validación
│   ├── 07-progresion.md              # Variables progresables, descargas y objetivos medibles
│   ├── 08-registro-y-evaluacion.md   # Registro diario mínimo y evaluación semanal
│   ├── 09-fuentes-de-datos-e-inferencias.md  # Qué se declara, qué se registra y qué se infiere
│   ├── 10-roadmap-del-producto.md    # Fases del producto (0–12) y puerta de entrada a la app
│   ├── 11-glosario-y-modelo-de-dominio.md  # Definiciones únicas de conceptos y entidades
│   ├── 12-modelo-de-carga-e-inferencia.md  # Dimensiones de carga, decaimiento, dosis y BJJ estimado
│   ├── roles/               # Orquestación opcional de dos IAs (ver sección más abajo)
│   └── superpowers/         # Planes de trabajo para ese flujo
├── opencode.json            # Agentes del orquestador en el flujo de dos IAs
└── data/
    ├── perfil.yaml      # Datos del atleta: medidas, objetivos, BJJ, fuerza, movilidad, material, consideraciones
    └── ejercicios.yaml  # Catálogo de ejercicios con metadatos y prescripción
```

Nota: `docs/00-contexto-completo-del-programa.md` es un documento agregador que concentra el contexto completo del programa para lectores (humanos o IA) que lleguen sin contexto previo. El detalle normativo vive en los documentos `01`–`09`; si editas uno de ellos, comprueba si el cambio debe reflejarse también en `00` para no dejarlos desincronizados.

Nota: `docs/10-roadmap-del-producto.md` define las fases del producto (0–12) y la puerta de entrada a la aplicación (fases 0–6 cerradas). No empieces trabajo de implementación de la app sin comprobar esa puerta; el README resume el estado actual.

## Cómo trabajar en este proyecto

- **No hay comandos de build, lint ni test.** No existe `package.json`, `pyproject.toml`, `Cargo.toml` ni ningún otro manifiesto: la "compilación" es la coherencia del contenido. Si se añade una app en el futuro, este archivo debe actualizarse con sus comandos.
- La única validación técnica posible hoy es la sintaxis YAML. Tras modificar cualquier archivo de `data/`, compruébalo, por ejemplo con:
  `python3 -c "import yaml; yaml.safe_load(open('data/ejercicios.yaml'))"`
- Tras cualquier cambio relevante, actualiza `CHANGELOG.md` y, si cambia la estructura o las convenciones, también `README.md` y este `AGENTS.md`.

## Convenciones

### Idioma y estilo

- Todo el contenido del repositorio está en **español** (documentos, valores YAML, texto visible). Mantén el español en cualquier archivo nuevo. La excepción son los mensajes de commit y los `id` de ejercicios, que van en inglés (ver abajo).
- Los documentos de `docs/` usan títulos `##` con secciones cortas y listas; el tono es prescriptivo y directo (reglas, no ensayos).
- Los archivos de `docs/` se numeran con prefijo `NN-` que define el orden de lectura; conserva la numeración al añadir documentos.

### Modelo de datos YAML

`data/ejercicios.yaml`:

- Empieza con `version: 2` y una sección `valores` que enumera los dominios válidos de los campos categóricos (`impacto_lumbar`, `compatibilidad_bjj`, `nivel`, `lateralidad`, `nivel_coste`, `dimensiones`, `patron`). **Los valores nuevos deben respetar esos dominios**; si se amplía un dominio, actualiza la sección `valores` primero. El dominio `patron` es la taxonomía cerrada de `docs/05`: un patrón nuevo se documenta allí antes de usarse.
- La lista de ejercicios cuelga de la clave `exercises`.
- Cada ejercicio tiene: `id` (kebab-case en inglés, ej. `kb-swing-two-hand`), `nombre` (español), `patron` (de la taxonomía de `docs/05`), `secundarios` (opcional, misma taxonomía), `material` (lista; cada elemento debe corresponderse con el inventario de `perfil.yaml → material` por concepto: ej. `kettlebell` ↔ `kettlebells_kg`, `goma` ↔ `gomas`, `cinta` ↔ `cinta_velocidad_max_kmh`), `nivel`, `lateralidad`, `coste_dimensiones` (mapa dimensión → bajo/medio/alto, dimensiones de `docs/12`), `impacto_lumbar`, `compatibilidad_bjj`, `objetivos` y, normalmente, `prescripcion`. Opcionales: `explosivo`, `isometrico`, `progresiones`, `regresiones`, `sustitutos` (referencias a otros `id` del catálogo; deben existir).
- Las prescripciones usan rangos de dos elementos (`series: [3, 5]`, `repeticiones: [8, 15]`) o valores fijos, más flags booleanos opcionales (`por_lado`, `evitar_fallo`, `detener_si_falla_tecnica`, etc.).

`data/perfil.yaml`: claves snake_case en español; los rangos se expresan como mapas `{min, max}`.

### Consistencia entre documentos

Los conceptos se repiten deliberadamente entre archivos y deben mantenerse coherentes:

- Las definiciones de los conceptos del dominio viven en `docs/11` y son únicas: si otro documento usa un término con otro significado, se corrige el otro documento.
- Los tres tipos de día (`02`) corresponden a las plantillas de sesión A–C (`06`) y a las ramas del árbol de decisión (`03`).
- El semáforo verde/amarillo/rojo de recuperación (`04`) es el mismo vocabulario que usa `impacto_lumbar` en los ejercicios.
- El material de los ejercicios debe corresponderse con el inventario de `perfil.yaml`.
- Reglas de seguridad dominantes (no negociables al editar): no programar sesiones de alto coste lumbar antes de BJJ normal o duro; evitar dos estímulos altos lumbares el mismo día; un día rojo es recuperación o descanso.

### Git

- Mensajes de commit cortos en inglés con prefijo de tipo: `docs:`, `data:`, `chore:` (ej. `docs: add decision engine`).
- No hay CI ni hooks. Por defecto, commits directos sobre la rama principal.
- Excepción: cuando se trabaja con el **flujo de dos IAs** (`docs/roles/`), se trabaja siempre en ramas — una rama = una tarea = un PR — y los PRs los fusiona el revisor, nunca el orquestador.

## Flujo de trabajo con dos IAs (opcional)

Existe una orquestación de agentes lista para usar en `docs/roles/` (ver su `README.md`): un orquestador/implementador (OpenCode, agentes definidos en `opencode.json`) ejecuta un plan de `docs/superpowers/plans/` tarea a tarea, y un revisor externo (Kimi o Claude, invocado por CLI) valida y fusiona los PRs. En este flujo, la «suite en verde» es la validación YAML + la coherencia entre documentos descritas en «Cómo trabajar en este proyecto». Las variantes `*-kimi.md` y `*-claude.md` de cada rol deben mantenerse sincronizadas: cualquier cambio al bucle se aplica a ambas en el mismo commit.

## Seguridad y sentido común

Este repositorio describe decisiones de entrenamiento reales para una persona con episodios lumbares recientes (`perfil.yaml → consideraciones`). Al modificar reglas, plantillas o ejercicios, **no elimines ni relajes las restricciones de seguridad lumbar** (semáforo, `impacto_lumbar: rojo`, límites de doble sesión) sin una instrucción explícita. Los datos de `perfil.yaml` son datos personales de salud y condición física: trátalos con discreción y no los expongas fuera del repo.
