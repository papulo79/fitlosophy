# Changelog

## 0.17.0 - Rediseño oscuro del frontend

- Rediseño visual y de usabilidad del MVP según `docs/superpowers/specs/2026-08-03-redisenio-frontend-mvp-design.md`: tema oscuro deportivo con acento lima (tokens en `app.css` con `@theme` de Tailwind 4), Barlow Condensed + Inter autoalojadas (`@fontsource`, únicas dependencias nuevas) e iconos de relleno propios (`Icon.svelte`, sin librería).
- Componentes nuevos: `SliderDolor` (0–10 con gradiente semáforo), `Chips` (material, con Todo/Nada y tatami fijo), `BarraProgreso` («n de m» en Ejecución); `Opciones` pasa a control segmentado oscuro conservando su API.
- Usabilidad móvil: objetivos táctiles ≥ 44 px, recuperación con texto «Bien/Regular/Mal» (los valores de API no cambian), NavBar con iconos y logout reubicado a Perfil.
- Sin cambios funcionales: misma API, mismos payloads, mismos stores y router; el contenido de seguridad (violaciones, incertidumbres, congelación) se conserva destacado. Verificado con capturas de las 7 pantallas y suite del backend intacta (58 tests).
- Identidad del proyecto: marca «mancuerna en diagonal» lima sobre oscuro como `logo.svg`, `icono.svg` + PNGs (180/192/512) y `favicon.svg` en `app/frontend/public/`; la cabecera y el login llevan la marca, e `index.html` enlaza favicon, apple-touch-icon y `theme-color`. La cabecera solo se muestra con sesión iniciada (el login ya no duplica el título) y los ítems del historial muestran la dosis en su propia línea (nada de cortes a mitad de palabra).
- Ayuda de ejercicios: cada nombre de ejercicio en Propuesta y Ejecución enlaza a una búsqueda de vídeo en YouTube (nueva pestaña, icono de lupa), para quien no conoce todavía todos los movimientos.

## 0.16.0 - Corrección completa de registros (criterio 7 de docs/14)

- Nuevo endpoint `PUT /api/sesiones/{id}/items/{item_id}`: corrige el registro de un ítem ya finalizado (estado, ejercicio real, dosis real, motivo). La dosis real corregida sustituye a la prevista — se recalculan los `puntos_reales` del ítem (incluido el ×1.25 por volumen sobre rango de `docs/12`) — y con ellos la carga de los días siguientes (criterio 4). Con la sesión en curso se rechaza (409): ahí se marca con PATCH.
- Lógica compartida entre PATCH (marcado en ejecución) y PUT (corrección posterior): mismo guardado de estado y mismas advertencias de reglas duras en sustituciones.
- Frontend (Historial): corrección por ítem con modal (completado / con cambios / sustituido / no realizado, valores reales y motivo) y corrección del cierre en línea (sensación + molestias); el detalle del día muestra además las dimensiones congeladas por el cierre.
- Tests formales del criterio 7: dosis corregida → carga recalculada desde el historial persistido; dosis sobre rango → puntos ×1.25; cierre corregido sin molestias → dimensión descongelada; PUT rechazado con sesión en curso. 58 tests en total, suite en verde.

## 0.15.0 - Tests E2E del flujo completo

- Dos pruebas funcionales nuevas que cierran la cobertura del criterio 2 de `docs/14` (flujo extremo a extremo) por los caminos que faltaban:
  - `test_flujo_completo_con_bjj_y_sustitucion_en_ejecucion`: BJJ declarado + estado diario → familia A, marcado por las cuatro vías del modal de ejecución (incluida la **sustitución con ejercicio real**, que solo se registraba en la interfaz), validaciones 422 del esquema (sustituido sin `exercise_id_real`, modificado sin valores reales), finalizar con recálculo del sustituto, cierre con congelación lumbar y verificación del historial (física + BJJ, `exercise_id_real` persistido).
  - `test_flujo_sin_material_e2e`: modo sin material (vacaciones/viaje, `docs/14`) de extremo a extremo hasta el historial, con el check por defecto al finalizar.
- Verificados con prueba de mutación: el test del flujo con BJJ detecta la pérdida del `exercise_id_real` en el PATCH de ítems (rojo con mutación, verde al revertir).
- `*.db` añadido a `.gitignore`: la BD SQLite local de desarrollo no se versiona.

## 0.14.0 - Frontend del MVP (Svelte 5 + Tailwind 4)

- Nueva `app/frontend/`: aplicación responsive con las 6 pantallas del MVP (`docs/14`) más login: estado diario (con selector de material disponible), propuesta (con sustitución validada y motivo del rechazo visible), ejecución (check por ítem + modal de desviación), cierre, historial (registro/corrección de BJJ, corrección de RPE) y perfil (JSON editable + exportación).
- Router por hash propio (sin dependencias): en producción basta servir `dist/` con `StaticFiles(html=True)`; en desarrollo, proxy de `/api` a uvicorn (puerto 8000).
- Backend: la API sirve el frontend compilado si existe (`app/frontend/dist`) y expone `GET /api/ejercicios` (catálogo ligero para el selector de sustituciones).
- `package-lock.json` incluido; `node_modules/` y `dist/` ignorados.
- Fix de un test dependiente de la hora del día: `test_bjj_registro_correccion_y_carga` construía el BJJ «hace 20 h», que de 20:00 a 23:59 locales caía en el día actual y no disparaba la regla C4 (el motor usa el día natural anterior, `docs/03`). La fecha ahora se construye ayer a la misma hora + 1 min (edad ≈ 23 h 59 min, ventana ×1.0 de `docs/12`).

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
