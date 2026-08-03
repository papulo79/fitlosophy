# Changelog

## 0.8.0 - Generador de sesiones

- `docs/06` reescrito como generador completo: bloques B0-B4, plantillas por familia A-D y reglas de composición, dosificación, sustitución y validación final contra el presupuesto.
- Reglas nuevas: B0/B4 no computan en el presupuesto; la dosis mínima reduce a la mitad el coste bajo (familias A y C).
- Ejemplo completo coherente con `docs/12`: familia A con lumbar, bisagra y agarre cargadas, validación numérica paso a paso y ejemplo de sustitución rechazada.
- Valores provisionales del generador identificados.

## 0.7.0 - Motor de decisión formal

- `docs/03` reescrito: cuestionario diario mínimo definitivo, reglas duras (D1-D6), de carga (C1-C6) y de preferencia (P1-P3) con orden de prioridad explícito.
- Flujo completo en pseudocódigo: del estado diario a familia de sesión, presupuesto por dimensión y patrones prioritarios/restringidos.
- Matriz de tipos de sesión (semáforo × BJJ × carga total) y formato de explicación esperada para cada decisión.
- Valores provisionales del motor identificados (umbral de dolor, factor de presupuesto compatible, ausencia de patrón).

## 0.6.0 - Ampliación de la biblioteca

- `data/ejercicios.yaml` pasa a `version: 2`: el coste escalar se sustituye por `coste_dimensiones` (mapa dimensión → bajo/medio/alto, según `docs/12`).
- Nuevos metadatos en todos los ejercicios: `nivel`, `lateralidad`, flags `explosivo`/`isometrico` y enlaces de `progresiones`, `regresiones` y `sustitutos`.
- 5 ejercicios nuevos: plancha frontal, dead bug, press militar con kettlebell, flexión en pica y dominada asistida con goma. Los 15 patrones de la taxonomía tienen ahora al menos un ejercicio.
- Nuevos dominios en `valores`: `nivel`, `lateralidad`, `nivel_coste` y `dimensiones`. El antiguo dominio `coste` desaparece.

## 0.5.0 - Modelo de carga e inferencia

- Nuevo `docs/12`: dimensiones de carga definitivas, ventanas y decaimiento, puntuación provisional, ajustes por dosis, carga estimada del BJJ y reglas de acumulación e inferencia.
- Ejemplo completo de cálculo en pseudocódigo (exceso de bisagra y agarre tras swing + peso muerto + BJJ).
- `docs/09` y `docs/04` actualizados para referenciar el modelo; todos los valores numéricos marcados como provisionales (calibración en Fase 9).

## 0.4.0 - Taxonomía de patrones

- Taxonomía cerrada de 15 patrones de movimiento en `docs/05`, con criterios de asignación y dimensiones que alimenta cada patrón.
- Nuevo dominio `patron` en `data/ejercicios.yaml → valores`; todos los ejercicios validados contra él.
- Nuevo campo opcional `secundarios` para patrones secundarios (swing a una mano, windmill, remo unilateral).
- Patrones sin ejercicio identificados para la ampliación de la biblioteca: `core_antiextension`, `empuje_vertical`.

## 0.3.0 - Glosario y modelo de dominio

- Nuevo `docs/11`: glosario con definiciones únicas y modelo de entidades (Fase 1 del roadmap).
- Decisiones de modelado cerradas: propuesta ≠ realizada, ejercicio ≠ variante ≠ dosis, carga multidimensional.
- Valores provisionales identificados (dimensiones de carga, taxonomía de patrones, decaimiento).
- Estado del diseño actualizado en `docs/00`.

## 0.2.0 - Roadmap y fuentes de datos

- Documento agregador `docs/00` con el contexto completo del programa.
- Roadmap del producto (`docs/10`): fases 0–12, criterios de entrada/salida y puerta de entrada a la aplicación.
- Especificación de fuentes de datos e inferencias (`docs/09`): datos declarados, registrados y derivados.
- README alineado con la numeración de fases del roadmap.
- `AGENTS.md` con la guía para agentes y el flujo opcional de dos IAs (`docs/roles/`, `docs/superpowers/`, `opencode.json`).

## 0.1.0 - Inicial

- Estructura base del repositorio.
- Perfil y objetivos iniciales.
- Filosofía del sistema adaptativo.
- Motor de decisión diario.
- Gestión de carga.
- Biblioteca inicial de ejercicios.
- Modelo YAML preparado para una futura aplicación web.
