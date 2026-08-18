# Glosario y modelo de dominio

## Propósito

Este documento es la fuente única de definiciones del sistema. Cada concepto usado por el motor de decisión, la biblioteca o el registro tiene aquí una definición única. Si otro documento usa un término con un significado distinto, prevalece este documento y el otro se corrige.

No define almacenamiento, API ni formato de persistencia. Los campos de las entidades son conceptuales: la futura implementación puede elegir base de datos, archivos o memoria sin reinterpretar el dominio.

Corresponde a la Fase 1 del roadmap (`docs/10`).

## Origen de los datos

Todo dato del sistema pertenece a una de estas cuatro categorías (detalle en `docs/09`):

- **Declarado**: lo aporta el usuario porque el sistema no puede conocerlo (dolor, sueño, tiempo disponible, posibilidad de BJJ).
- **Registrado**: lo que ocurrió realmente (sesiones físicas, BJJ, respuestas posteriores).
- **Biblioteca**: conocimiento estático sobre ejercicios y patrones (`data/ejercicios.yaml`).
- **Inferido**: lo que el motor deriva de los tres anteriores (carga activa, presupuestos, recomendación).

El sistema distingue además entre dato conocido, estimado y desconocido, y actúa de forma conservadora ante la incertidumbre.

## Glosario

- **Bloque**: parte funcional de una sesión (calentamiento, bloque principal, acondicionamiento, vuelta a la calma). Una sesión se compone de bloques ordenados.
- **Carga**: estímulo de entrenamiento acumulado sobre el organismo. Nunca es un único valor global: se descompone por dimensiones y por ventanas temporales.
- **Carga activa**: parte de la carga de sesiones pasadas que sigue sin recuperarse en el momento de decidir. Decae con el tiempo.
- **Carga externa**: peso o resistencia añadida al cuerpo (kettlebell, goma, lastre). El peso corporal no es carga externa.
- **Coste**: fatiga que un ejercicio o sesión produce por dimensión de carga. No es fijo: el coste base de la biblioteca se ajusta por la dosis y la respuesta individual.
- **Descarga**: periodo (normalmente una semana) de volumen reducido para disipar fatiga acumulada. Se activa por señales, no por calendario.
- **Dimensión de carga**: eje independiente en el que se mide el coste: total, lumbar, bisagra, rodilla y piernas, hombro y codo, agarre, core, cardio e impacto articular.
- **Dolor**: síntoma declarado por el usuario, con intensidad (0-10) y zona. Un dolor que altera el movimiento es una restricción de seguridad, no una preferencia.
- **Dosis**: cuánto se hace de un ejercicio en una sesión concreta: series, repeticiones o tiempo, carga externa, descansos, proximidad al fallo. La misma variante con distinta dosis produce distinto impacto.
- **Estado diario**: conjunto de datos declarados e inferidos que describen al usuario en el momento de decidir la sesión.
- **Familia de sesión**: tipo de sesión que el motor selecciona antes de concretar ejercicios. Corresponde a las plantillas A–D de `docs/06` y a los tipos de día de `docs/02`.
- **Incertidumbre**: falta de datos relevantes para una decisión. Se representa explícitamente; nunca se rellena inventando datos.
- **Limitación**: restricción de movimiento declarada o registrada. Puede ser permanente o temporal.
- **Material**: equipamiento disponible para entrenar. Su inventario vive en `data/perfil.yaml`; los ejercicios solo pueden requerir material existente.
- **Molestia**: dolor o síntoma de baja intensidad que no llega a limitar el movimiento. Se registra porque su repetición alimenta las reglas de seguridad.
- **Objetivo**: cualidad que el usuario quiere mejorar, con prioridad explícita (perder grasa, técnica de BJJ, evitar lesiones, fuerza, cardio, músculo).
- **Patrón de movimiento**: clasificación biomecánica de un ejercicio (empuje horizontal, dominante de cadera, antirotación...). Taxonomía cerrada en `docs/05`; un ejercicio tiene un patrón principal y puede declarar secundarios.
- **Presupuesto de carga**: cantidad máxima de carga por dimensión que la sesión del día puede consumir sin violar las reglas. Lo fija el motor antes de generar la sesión.
- **Progresión / regresión**: variante más difícil / más fácil del mismo patrón. Permiten ajustar la dificultad sin cambiar el objetivo de la sesión.
- **Recuperación (semáforo)**: estado verde, amarillo o rojo según sueño, fatiga, dolor y movilidad (`docs/04`). Un día rojo es recuperación o descanso; la motivación no lo convierte en verde.
- **Regla**: condición del motor con prioridad definida. Reglas duras (seguridad, no negociables), reglas de carga (presupuestos) y reglas de preferencia (objetivos, motivación). Una preferencia nunca anula una regla dura.
- **RPE**: esfuerzo percibido de 1 a 10. Se registra el previsto y el real; su diferencia calibra el sistema.
- **Sesión de BJJ**: entrenamiento de jiu-jitsu, clasificado como técnico, normal o duro. Es parte central de la carga, no un evento aparte.
- **Sesión física**: entrenamiento físico propuesto o realizado, distinto del BJJ.
- **Sesión propuesta / sesión realizada**: lo que el sistema recomienda frente a lo que el usuario hizo. Son entidades distintas: la comparación entre ambas alimenta la calibración.
- **Sustituto**: ejercicio que puede reemplazar a otro cumpliendo el mismo objetivo y patrón dentro de una sesión, sin invalidarla.
- **Variable derivada**: dato inferido por el motor a partir del historial y la biblioteca (carga activa por dimensión, tiempo desde el último estímulo de un patrón, necesidad de descarga).
- **Variante**: forma concreta de ejecutar un ejercicio (a una mano, con pausa, asistida). Un ejercicio puede tener varias variantes con distinto coste y nivel.

## Entidades

### Usuario

El atleta que usa el sistema. Un despliegue puede tener varios (uso familiar, `docs/14`).

- Obligatorio: identificador de acceso y credencial.
- Origen: declarado. Se da de alta fuera de la aplicación, en el servidor.
- Relaciones: **es el dueño de todo lo demás.** Perfil, estados diarios, propuestas, sesiones realizadas, registros de BJJ y respuestas posteriores pertenecen a un usuario y solo tienen sentido dentro del suyo. El historial y la carga activa se calculan por usuario.
- No es dueño de la biblioteca de ejercicios ni del vocabulario del modelo: esos son comunes al despliegue.

### Perfil

Quién es el usuario y qué condiciona todas las decisiones. Hay uno por usuario.

- Obligatorio: medidas básicas, objetivos ordenados, material disponible, consideraciones de salud.
- Opcional: capacidades conocidas, horario habitual de BJJ.
- Origen: declarado. Persiste entre sesiones; cambia poco.
- Relaciones: pertenece a un usuario; tiene objetivos, material y restricciones permanentes.

### Objetivo

- Obligatorio: cualidad, prioridad.
- Opcional: métrica asociada, horizonte temporal.
- Origen: declarado.

### Estado diario

- Obligatorio: fecha, recuperación (semáforo), posibilidad de BJJ, dolor (0-10; con zona si es mayor que 0).
- Opcional: limitación, sueño, tiempo disponible, intensidad prevista del BJJ, preferencia o motivación, circunstancias extraordinarias.
- Origen: declarado; efímero (válido para un día).
- Nota: el dolor se declara siempre, aunque sea 0, para que «no declarado» nunca se confunda con «sin dolor». El descanso general sin dolor concreto se expresa con el semáforo (amarillo o rojo), no con el dolor.

### Ejercicio

- Obligatorio: identificador estable, nombre, patrón principal, material, coste base por dimensiones, impacto lumbar, compatibilidad con BJJ.
- Opcional: patrones secundarios, nivel, lateralidad, comportamiento (controlado/explosivo, dinámico/isométrico), restricciones, progresiones, regresiones, sustitutos, prescripción orientativa.
- Origen: biblioteca (`data/ejercicios.yaml`). El coste base se declara por dimensión (`coste_dimensiones`); los valores concretos son provisionales y se calibran en la Fase 9.

### Variante de ejercicio

- Obligatorio: ejercicio al que pertenece, descripción de la variación.
- Opcional: ajuste de coste respecto al ejercicio base, nivel.
- Origen: biblioteca. Hoy las variantes viven mezcladas como ejercicios independientes; su separación formal es pendiente.

### Patrón de movimiento

- Obligatorio: nombre, criterio de asignación, dimensiones de carga que alimenta.
- Origen: biblioteca. Taxonomía cerrada definida en `docs/05` y en `data/ejercicios.yaml → valores → patron`.

### Dimensión de carga

- Obligatorio: nombre, descripción de qué la alimenta.
- Origen: biblioteca. Lista definitiva en `docs/12`.

### Bloque de sesión

- Obligatorio: función del bloque, posición en la sesión.
- Opcional: duración objetivo, ejercicios asignados.
- Relaciones: pertenece a una sesión; contiene dosis de ejercicios.

### Sesión propuesta

- Obligatorio: fecha, familia de sesión, bloques con ejercicios y dosis, presupuesto de carga aplicado, explicación de la decisión.
- Origen: inferido.
- Relaciones: deriva del estado diario y del presupuesto; se compara con la sesión realizada.

### Sesión realizada

- Obligatorio: fecha, tipo, duración.
- Opcional: ejercicios y dosis reales, RPE real, cambios respecto a la propuesta, molestias durante o después.
- Origen: registrado.
- Relaciones: puede referenciar la sesión propuesta que modificó.

### Registro de BJJ

- Obligatorio: fecha, clasificación (técnico, normal, duro), duración.
- Opcional: tiempo de técnica, rondas, intensidad percibida, fatiga de agarre, incidencias.
- Origen: registrado.

### Molestia o limitación

- Obligatorio: zona, tipo (molestia o limitación), carácter (temporal o permanente).
- Opcional: intensidad, ejercicios relacionados, fecha de inicio y resolución.
- Origen: declarado o registrado.

### Respuesta posterior

- Obligatorio: sensación al terminar.
- Opcional: molestias posteriores, estado al día siguiente, tiempo de recuperación.
- Origen: registrado. Alimenta la calibración y las reglas de seguridad.

### Regla

- Obligatorio: condición, consecuencia, tipo (dura, de carga, de preferencia), prioridad.
- Origen: biblioteca. Reglas duras, de carga y de preferencia formalizadas con prioridad en `docs/03`; reglas de gestión de carga en `docs/04`.

### Variable derivada

- Obligatorio: nombre, fuentes (historial, biblioteca, estado diario), ventana temporal si aplica.
- Origen: inferido. Lista prevista en `docs/09`; cálculo y decaimiento en `docs/12` (valores provisionales).

### Presupuesto de carga

- Obligatorio: fecha, límite por dimensión.
- Origen: inferido a partir de la carga activa, el estado diario y la familia de sesión.

### Recomendación

- Obligatorio: familia de sesión seleccionada, motivos, restricciones aplicadas.
- Opcional: alternativas válidas, nivel de incertidumbre.
- Origen: inferido. Debe ser explicable (`docs/10`, explicabilidad transversal).

## Relaciones principales

```text
Usuario ──posee──▶ Perfil, Estado diario, Sesión propuesta, Sesión realizada, Registro de BJJ
Perfil ──tiene──▶ Objetivo, Material, Restricción permanente
Estado diario ──declarado por──▶ Perfil
Historial (de un usuario) = Sesiones realizadas + Registros de BJJ + Respuestas posteriores
Historial + Biblioteca ──inferencia──▶ Variables derivadas (carga activa por dimensión)
Estado diario + Variables derivadas ──reglas──▶ Familia de sesión + Presupuesto de carga
Familia + Presupuesto + Biblioteca ──generador──▶ Sesión propuesta (bloques, ejercicios, dosis)
Sesión propuesta ──comparación──▶ Sesión realizada ──produce──▶ Respuesta posterior
Ejercicio ──tiene──▶ Variante, Patrón, Coste por dimensión, Sustitutos
```

## Decisiones de modelado

Criterios de salida de la Fase 1 y cómo quedan resueltos:

- **Propuesta ≠ realizada**: son entidades separadas; su comparación es un dato de calibración.
- **Ejercicio ≠ variante ≠ dosis**: el ejercicio es el concepto, la variante una forma de ejecutarlo, la dosis cuánto se hace en una sesión concreta.
- **Carga multidimensional**: ninguna decisión se toma sobre un único valor global de carga.
- **Físicas y BJJ representables**: BJJ es una entidad de registro propia que alimenta las mismas dimensiones de carga.
- **Independencia de almacenamiento**: ningún campo conceptual presupone base de datos, API ni framework.

## Valores provisionales

- Coste base por dimensión de cada ejercicio (`coste_dimensiones` en `data/ejercicios.yaml`); se calibra en la Fase 9.
- Separación formal ejercicio/variante en `data/ejercicios.yaml`.
- Valores numéricos del modelo de carga (`docs/12`): decaimiento, puntos, umbrales y tabla de BJJ.
- Valores del motor de decisión (`docs/03`): umbral de dolor, factor de presupuesto compatible y umbral de ausencia de patrón.
- Valores del generador de sesiones (`docs/06`): duraciones y RPE de plantillas, reservas, reducción de coste con dosis mínima y orden de recorte.
