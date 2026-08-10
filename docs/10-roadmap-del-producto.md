# Roadmap del producto

## Propósito

Este documento define la evolución funcional de Fitlosophy como producto. No establece fechas ni decisiones técnicas prematuras. Cada fase tiene un objetivo, entregables y criterios de salida.

La aplicación no debe construirse solo porque ya exista una preferencia por React o Svelte. El desarrollo comienza cuando el modelo funcional puede validarse manualmente sin que quien lo ejecute tenga que improvisar reglas.

## Visión

Fitlosophy debe convertirse en una aplicación personal de entrenamiento adaptativo capaz de:

- Recoger el estado diario con poca fricción.
- Recuperar e interpretar el historial reciente.
- Inferir carga acumulada por patrones y zonas.
- Seleccionar una familia de sesión.
- Generar una propuesta explicable y modificable.
- Registrar la sesión realmente realizada.
- Registrar la respuesta posterior.
- Ajustar progresivamente sus estimaciones al usuario.

No diagnostica lesiones ni sustituye a profesionales sanitarios o del entrenamiento.

## Principios

1. Primero se diseña el conocimiento; después se construye la aplicación.
2. Cada fase debe producir resultados verificables.
3. Los valores provisionales deben identificarse como tales.
4. El sistema debe explicar sus decisiones.
5. El historial real tiene prioridad sobre la planificación no ejecutada.
6. El usuario aporta hechos subjetivos; el motor infiere la carga.
7. Toda lógica de diseño se expresa mediante reglas y pseudocódigo, no mediante implementación.

---

# Fase 0. Contexto y visión

## Objetivo

Concentrar el contexto personal, deportivo y funcional del problema.

## Entregables

- Perfil y objetivos priorizados.
- Filosofía del sistema.
- Alcance y límites.
- Material disponible.
- Escenarios diarios principales.
- Tipos iniciales de sesión.

## Criterios de salida

- Se entiende que el producto es adaptativo y no un calendario rígido.
- BJJ forma parte central del modelo de carga.
- Están documentados los escenarios principales y los límites de seguridad.

## Estado

Cerrada. Contexto, perfil y filosofía fijados en `docs/00`–`docs/02`.

---

# Fase 1. Modelo de dominio

## Objetivo

Definir los conceptos del sistema y sus relaciones sin decidir todavía base de datos, API o framework.

## Entregables

- Glosario de dominio.
- Entidades y relaciones.
- Campos conceptuales obligatorios y opcionales.
- Distinción entre ejercicio, variante y dosis.
- Distinción entre sesión propuesta y realizada.
- Separación entre datos declarados, registrados e inferidos.

## Criterios de salida

- Cada concepto tiene una definición única.
- El modelo representa sesiones físicas y BJJ.
- La carga se representa por varias dimensiones.
- La implementación futura no necesita reinterpretar el dominio.

## Estado

Cerrada. Modelo de dominio en `docs/11`, implementado en `fitlosophy/models.py`.

---

# Fase 2. Biblioteca de conocimiento

## Objetivo

Construir la biblioteca que permite interpretar ejercicios, variantes y actividades.

## Entregables

- Taxonomía de patrones.
- Taxonomía de dimensiones de carga.
- Biblioteca inicial para todo el material disponible.
- Compatibilidad con BJJ.
- Progresiones, regresiones y sustituciones.
- Criterios para incorporar ejercicios nuevos.

## Criterios de salida

- Los ejercicios habituales tienen metadatos suficientes.
- Se pueden generar sesiones variadas sin usar ejercicios no catalogados.
- El motor puede inferir carga lumbar, bisagra, agarre, empuje, tirón, piernas y cardio.

## Estado

Cerrada en su primera versión. `docs/05` y `data/ejercicios.yaml`: 28 ejercicios con patrón, material, coste por dimensión, impacto lumbar, prescripción, descripción de ejecución e intención. Seguirá creciendo con el uso.

---

# Fase 3. Modelo de carga e inferencia

## Objetivo

Definir cómo la biblioteca y el historial se transforman en conocimiento útil para la siguiente decisión.

## Entregables

- Dimensiones de carga definitivas.
- Modelo conceptual de dosis.
- Ventanas temporales.
- Reglas de acumulación y decaimiento.
- Tratamiento de dobles sesiones.
- Influencia del RPE y de la respuesta posterior.
- Tratamiento de incertidumbre y datos incompletos.

## Criterios de salida

- Un historial de ejemplo produce una carga activa explicable.
- El usuario no tiene que declarar que hizo demasiada bisagra, tirón o agarre.
- Se diferencia carga observada, estimada y desconocida.
- Los ejemplos están expresados en pseudocódigo o reglas funcionales.

## Estado

Cerrada. `docs/12` implementado en `fitlosophy/load.py`, con su aritmética verificada en `test_load.py`.

---

# Fase 4. Motor de decisión

## Objetivo

Definir la secuencia que transforma el estado diario y el historial en una familia de sesión y un presupuesto de carga.

## Entregables

- Cuestionario diario mínimo.
- Reglas de seguridad.
- Reglas de carga.
- Reglas de preferencia.
- Prioridad entre reglas.
- Árboles y flujos en pseudocódigo.
- Matriz de tipos de sesión.
- Formato de explicación de la decisión.

## Criterios de salida

- Los escenarios principales producen decisiones coherentes.
- La motivación no puede anular una restricción.
- La ausencia de BJJ no obliga a entrenar fuerte.
- La disponibilidad incierta de BJJ conserva margen.
- Los conflictos entre reglas están resueltos.

## Estado

Cerrada. `docs/03` implementado en `fitlosophy/engine.py`; las reglas D/C/P se citan en la explicación de cada propuesta.

---

# Fase 5. Generador de sesiones

## Objetivo

Definir cómo se construye una sesión concreta una vez elegidos su familia, patrones y presupuesto.

## Entregables

- Plantillas por familia de sesión.
- Reglas de composición y orden.
- Reglas de volumen, intensidad y descansos.
- Reglas de sustitución.
- Adaptación al tiempo disponible.
- Validación del coste combinado.

## Criterios de salida

- Se generan sesiones completas para los escenarios principales.
- Se respetan presupuestos globales y locales.
- Una sustitución mantiene el objetivo de la sesión.
- Cada bloque tiene una justificación.

## Estado

Cerrada. `docs/06` implementado en `fitlosophy/generator.py`, incluidas composición, dosificación, sustitución y validación.

---

# Fase 6. Casos de uso y validación manual

## Objetivo

Validar el diseño antes de construir software.

## Entregables

- Casos normales y casos límite.
- Semanas simuladas.
- Casos con datos incompletos.
- Casos con dolor o limitación.
- Cambios inesperados de disponibilidad de BJJ.
- Propuestas rechazadas o modificadas.
- Registro de contradicciones y decisiones provisionales.

## Criterios de salida

- El sistema resuelve una muestra amplia sin improvisación.
- No pregunta al usuario datos que puede inferir.
- Las recomendaciones son trazables y comprensibles.
- Existe una base de casos reutilizable como pruebas funcionales.

## Estado

Cerrada. Los 10 casos de `docs/13` son pruebas ejecutables en `test_cases.py`.

---

# Puerta de entrada a la aplicación

> **Puerta superada.** Las fases 0 a 6 se cerraron y el modelo funcional validable se alcanzó antes de escribir la aplicación. Esta sección se conserva porque su criterio sigue vigente para cualquier ampliación futura del modelo: primero se documenta, después se construye.

La construcción de la aplicación no debe comenzar hasta que las **fases 0 a 6** estén suficientemente cerradas.

No se exige una precisión matemática definitiva, pero sí:

- Contexto y alcance estables.
- Modelo de dominio estable.
- Biblioteca inicial utilizable.
- Modelo de carga coherente.
- Cuestionario diario definido.
- Motor de decisión formalizado.
- Plantillas de sesión definidas.
- Casos de uso validados manualmente.
- Decisiones provisionales identificadas.

El hito que abre la puerta al desarrollo se denomina **modelo funcional validable**.

---

# Fase 7. Diseño del MVP

## Objetivo

Definir la primera aplicación útil y sus criterios de aceptación.

## Funcionalidades del MVP

### Perfil

- Datos básicos.
- Objetivos y prioridades.
- Material disponible.
- Restricciones permanentes o temporales.

### Estado diario

- Dolor, zona y limitación.
- Recuperación y sueño percibidos.
- Tiempo disponible.
- Posibilidad e intensidad prevista de BJJ.
- Preferencia opcional.

### Historial

- Registro de BJJ.
- Registro de sesión física.
- Ejercicios, dosis y RPE real.
- Cambios respecto a la propuesta.
- Respuesta posterior.

### Recomendación

- Selección de familia de sesión.
- Generación de propuesta.
- Explicación de motivos y restricciones.
- Sustituciones compatibles.
- Reducción de duración o carga.

## Fuera del MVP

- Integraciones con wearables.
- Aprendizaje automático.
- Nutrición completa.
- Funciones sociales.
- Diagnóstico de lesiones.
- Automatización sin supervisión.

## Criterios de salida

- Pantallas y flujos definidos.
- Alcance cerrado.
- Criterios de aceptación funcionales.
- Correspondencia clara entre funcionalidades y dominio.

## Estado

Cerrada. `docs/14` define pantallas, flujo de uso y los 9 criterios de aceptación funcionales.

---

# Fase 8. Construcción del MVP

## Objetivo

Implementar el MVP. La elección entre React, Svelte u otra tecnología pertenece a esta fase.

## Flujo mínimo

```text
Declarar estado diario
→ recibir propuesta
→ aceptar o modificar
→ registrar sesión real
→ registrar respuesta posterior
→ conservar historial
```

## Criterios de salida

- Flujo principal completo.
- Decisiones trazables.
- Casos funcionales principales superados.
- Datos editables y exportables.
- Incertidumbre visible.

## Estado

Cerrada. La aplicación está desplegada y en uso: FastAPI + SQLite (`fitlosophy_api`) y Svelte 5 + Tailwind 4 (`app/frontend`), un único proceso sirviendo API y frontend tras un túnel de Cloudflare. Los 9 criterios de `docs/14` están cubiertos y la suite tiene 98 tests en verde.

---

# Fase 9. Uso personal y calibración

## Objetivo

Usar el MVP con datos reales para ajustar el modelo.

## Actividades

- Comparar propuesta y ejecución.
- Analizar recomendaciones rechazadas.
- Detectar sustituciones habituales.
- Relacionar sesiones con respuesta posterior.
- Ajustar costes individuales.
- Reducir campos que generen fricción sin aportar valor.

## Criterios de salida

- Existe historial real suficiente.
- Se han identificado errores sistemáticos.
- Los costes principales han sido recalibrados.
- Las recomendaciones resultan útiles de forma consistente.

## Estado

En curso desde el 10 de agosto de 2026. Empieza el uso diario con datos reales; los valores numéricos de `docs/12` siguen siendo provisionales y es esta fase la que debe calibrarlos.

---

# Fase 10. Producto personal completo

## Objetivo

Convertir el MVP calibrado en una herramienta personal madura.

## Funcionalidades previstas

- Panel de carga por dimensiones.
- Vista semanal y mensual.
- Evolución de fuerza y capacidad.
- Alertas de acumulación.
- Gestión de progresiones y descargas.
- Comparación entre propuesta, ejecución y respuesta.
- Edición completa de biblioteca y reglas configurables.

## Estado

No iniciada.

---

# Fase 11. Integraciones opcionales

## Objetivo

Incorporar fuentes externas solo cuando aporten valor demostrado.

## Posibles integraciones

- Wearables y frecuencia cardiaca.
- Sueño y actividad diaria.
- Importación y exportación de sesiones.
- Calendario.
- Notificaciones.

## Criterios

- Ninguna integración sustituye la percepción del usuario.
- Los datos externos deben identificar su calidad e incertidumbre.
- El sistema debe funcionar sin servicios externos.

## Estado

No iniciada.

---

# Fase 12. Adaptación avanzada

## Objetivo

Personalizar progresivamente las recomendaciones usando el historial individual.

## Funcionalidades previstas

- Ajuste de costes por respuesta observada.
- Detección de combinaciones asociadas a molestias.
- Identificación de dosis bien toleradas.
- Ajuste de ventanas de recuperación.
- Priorización basada en adherencia y preferencias reales.

No implica necesariamente aprendizaje automático. Puede comenzar con reglas transparentes y ajustes supervisados.

## Estado

No iniciada.

---

# Próximo hito

**Calibrar el modelo con uso real** (Fase 9).

El hito anterior —modelo funcional validable— se alcanzó, y con él se construyó y desplegó el MVP. Lo que queda ya no se programa: se entrena. Todos los valores numéricos de `docs/12` (puntos por nivel de coste, multiplicadores de dosis, ventanas de decaimiento) se declararon provisionales a la espera de datos propios.

Se considerará alcanzado cuando exista historial real suficiente para que:

- Las propuestas rechazadas o modificadas de forma sistemática revelen dónde el generador se equivoca.
- El RPE real contrastado con el previsto permita ajustar los costes por dimensión.
- La respuesta posterior valide —o corrija— el criterio lumbar, que es la restricción de seguridad dominante del sistema.
- Los campos que generan fricción sin aportar valor se identifiquen y se retiren.

Los datos necesarios ya se persisten y se exportan con `GET /api/export`: no hace falta registrar nada aparte del uso normal.
