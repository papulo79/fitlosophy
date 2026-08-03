# Changelog

## 0.13.0 - API REST del MVP

- Nuevo paquete `fitlosophy_api` (FastAPI + SQLite stdlib): auth de usuario único (pbkdf2, cookie HttpOnly de 30 días), sin registro.
- Flujo completo del MVP como endpoints: estado diario → propuesta (con explicación e incertidumbre) → sustitución validada → sesión con marcado por ítem (completado/modificado/sustituido/no_realizado) → finalizar con RPE real → cierre con congelación de ventana tras molestia.
- Historial (días, detalle propuesta vs realizado), registro y corrección de BJJ, perfil editable, exportación JSON completa.
- El recálculo con dosis real y la congelación de dimensiones se implementaron en el núcleo `fitlosophy` (sin duplicar lógica).
- 12 tests de API nuevos (53 en total): acceso exigido, flujo E2E, rechazo 409 de sustituciones inválidas, congelación, correcciones y export.
- `scripts/init_db.py` y `app/backend/README.md` con instalación y arranque.

## 0.12.0 - Motor ejecutable en Python

- Nueva `app/backend/`: paquete `fitlosophy` (Python 3.11+, pyyaml) con el modelo de carga (`load.py`), el motor de decisión (`engine.py`, reglas D/C/P) y el generador de sesiones (`generator.py`) implementados según `docs/12`, `docs/03` y `docs/06`.
- 41 tests en verde: `test_load.py` (aritmética de `docs/12`) y `test_cases.py` (los 10 casos de `docs/13` como pruebas funcionales ejecutables).
- Correcciones de coherencia detectadas por la implementación: el ejemplo de `docs/12` omitía el agarre del peso muerto (agarre real 8, presupuesto 0 y tirón pendiente; actualizado en `docs/06` y `docs/13`); el sábado del caso 8 queda con agarre baja tras el decaimiento.
- AGENTS.md y README actualizados: el repo pasa a tener código ejecutable con suite de tests.

## 0.11.0 - Material disponible por día

- Nuevo input `material_disponible` en el estado diario (`docs/03`): selector del inventario del garaje con marcar/desmarcar todo; por defecto todo disponible. La lista vacía equivale al modo sin material (vacaciones, viajes); el tatami cuenta siempre como suelo.
- Filtro de material en el generador (`docs/06`, regla 9): solo entran ejercicios con el material requerido disponible; los patrones sin ejercicios posibles se declaran pendientes en la explicación.
- Nuevo flag `sin_material` en el catálogo para ejercicios válidos incluso sin nada: flexiones, pica, puente de glúteos, planchas y dead bug.
- Dos ejercicios nuevos sin material: sentadilla libre y zancada hacia delante (cobertura de `dominante_rodilla`).
- Limitación conocida: sin barra, TRX ni gomas no hay tirón con el catálogo actual; se declara en la explicación.

## 0.10.0 - Diseño del MVP

- Nuevo `docs/14`: definición del MVP (Fase 7) con el contexto de uso real (momento de decisión ~16:15, BJJ declarado a diario, material siempre de garaje).
- Seis pantallas definidas: estado diario, propuesta, ejecución con marcado por ítem (check + modal de modificación), cierre con «Finalizar», historial y perfil.
- Alcance del algoritmo en la primera versión y lista explícita de lo que queda fuera.
- Acceso por usuario y contraseña: aplicación privada de un único usuario.
- Ocho criterios de aceptación funcionales; los casos de `docs/13` se convierten en las pruebas del MVP.

## 0.9.0 - Validación manual con casos de uso

- Nuevo `docs/13`: 10 casos ejecutados a mano con la aritmética completa (familia B potente, familia A con BJJ, dolor lumbar, BJJ incierto, día rojo con motivación, día post-doble-sesión, datos incompletos, semana simulada completa, sustituciones y bisagra en días consecutivos).
- Incoherencias encontradas y corregidas: umbral exacto media/alta y presupuesto crítico (`docs/12`), definición operativa de «bisagra exigente» en D5 (`docs/03`).
- Comportamiento deliberado registrado para calibración: prohibición categórica de agarre medio/alto en familia A (I4).
- Fases 0-6 del roadmap cerradas; la puerta de entrada al desarrollo queda abierta en cuanto al diseño.

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
