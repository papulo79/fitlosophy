# Roadmap del producto

## Propósito

Este documento define la evolución de Fitlosophy como producto.

No es un calendario de fechas ni una planificación de desarrollo técnico. Es una secuencia de fases funcionales con objetivos, entregables, criterios de entrada y criterios de salida.

La construcción de la aplicación no debe comenzar por disponer de un framework elegido. Debe comenzar cuando el modelo funcional sea suficientemente estable para evitar que la interfaz y la persistencia condicionen decisiones todavía abiertas.

## Visión del producto

Fitlosophy debe convertirse en una aplicación personal de entrenamiento adaptativo capaz de:

- Recoger un estado diario con poca fricción.
- Recuperar el historial reciente.
- Inferir carga acumulada por patrones, zonas y tipos de fatiga.
- Elegir una familia de sesión adecuada.
- Generar una propuesta comprensible y modificable.
- Registrar lo realizado realmente.
- Comparar la propuesta con la respuesta posterior.
- Ajustar progresivamente las recomendaciones al usuario.

El producto no pretende sustituir a un entrenador, fisioterapeuta o profesional sanitario. Tampoco pretende diagnosticar lesiones.

## Principios del roadmap

1. Primero se diseña el conocimiento; después se construye la aplicación.
2. Cada fase debe producir algo verificable.
3. No se avanza por haber escrito documentación, sino por haber resuelto las decisiones necesarias.
4. Los valores provisionales deben identificarse como provisionales.
5. La aplicación inicial debe ser útil antes de incorporar aprendizaje automático o integraciones externas.
6. El sistema debe explicar sus decisiones.
7. El historial real tiene más valor que una planificación teórica no ejecutada.

---

# Fase 0. Contexto y visión

## Objetivo

Concentrar el contexto completo del problema y definir qué producto se quiere construir.

## Entregables

- Contexto personal y deportivo.
- Objetivos ordenados.
- Filosofía del sistema.
- Alcance y límites.
- Material disponible.
- Escenarios diarios principales.
- Definición inicial de los tipos de sesión.

## Criterios de salida

La fase se considera suficientemente cerrada cuando:

- Está claro que el producto es adaptativo y no un calendario rígido.
- Los objetivos tienen prioridad explícita.
- BJJ está integrado como parte central de la carga.
- Se conocen los escenarios que el sistema debe resolver.
- Se han documentado los límites sanitarios y de seguridad.

## Estado

Muy avanzada.

---

# Fase 1. Modelo de dominio

## Objetivo

Definir los conceptos del sistema y sus relaciones sin comprometerse todavía con una base de datos, una API o un framework.

## Entidades funcionales previstas

- Usuario o perfil.
- Objetivo.
- Estado diario.
- Ejercicio.
- Variante de ejercicio.
- Patrón de movimiento.
- Dimensión de carga.
- Sesión propuesta.
- Sesión realizada.
- Bloque de una sesión.
- Registro de BJJ.
- Molestia o limitación.
- Respuesta posterior.
- Regla.
- Inferencia.
- Presupuesto de carga.
- Recomendación.

## Entregables

- Glosario de dominio.
- Descripción de cada entidad.
- Campos conceptuales obligatorios y opcionales.
- Relaciones entre entidades.
- Separación entre datos declarados, registrados e inferidos.
- Identificación de datos históricos y datos temporales.

## Criterios de salida

- Cada concepto usado por el algoritmo tiene una definición única.
- Se diferencia claramente propuesta de sesión y sesión realizada.
- Se diferencia ejercicio de variante y de dosis.
- La carga no se reduce a un único valor global.
- El modelo permite representar sesiones físicas y BJJ.
- La futura implementación puede elegir almacenamiento sin reinterpretar el dominio.

## Estado

En curso.

---

# Fase 2. Biblioteca de conocimiento

## Objetivo

Construir una biblioteca suficientemente rica para que el motor pueda interpretar los ejercicios y no dependa de reglas escritas para cada caso concreto.

## Contenido de la biblioteca

Para cada ejercicio o variante:

- Nombre e identificador estable.
- Patrón principal y secundarios.
- Material requerido.
- Nivel o dificultad.
- Tipo de contracción o comportamiento relevante.
- Bilateral o unilateral.
- Controlado o explosivo.
- Coste base por dimensiones.
- Compatibilidad con BJJ.
- Restricciones conocidas.
- Posibles regresiones y progresiones.
- Formas de dosificación.
- Sustitutos funcionales.

## Entregables

- Taxonomía de patrones.
- Taxonomía de costes.
- Biblioteca inicial completa para el material disponible.
- Reglas de equivalencia y sustitución.
- Criterios para añadir nuevos ejercicios.

## Criterios de salida

- Se pueden construir sesiones variadas sin recurrir a ejercicios no catalogados.
- Los ejercicios más utilizados tienen metadatos suficientes.
- El sistema puede inferir carga de bisagra, lumbar, agarre, piernas, empuje, tirón y cardio.
- Existen progresiones y regresiones para los movimientos principales.
- Los ejercicios de coste alto están identificados sin considerarlos prohibidos.

## Estado

Iniciada, todavía incompleta.

---

# Fase 3. Modelo de carga e inferencia

## Objetivo

Definir cómo el historial y la biblioteca se transforman en conocimiento útil para decidir la siguiente sesión.

## Preguntas que debe resolver

- ¿Qué carga sigue activa después de una sesión?
- ¿Cómo decae con el tiempo?
- ¿Cómo se combinan varias sesiones?
- ¿Cómo se interpreta una doble sesión?
- ¿Cómo afecta el RPE real?
- ¿Cómo se diferencia volumen moderado de una dosis muy exigente del mismo ejercicio?
- ¿Cómo se incorpora una respuesta negativa al día siguiente?
- ¿Cómo se representa la incertidumbre cuando faltan datos?

## Entregables

- Dimensiones de carga definitivas.
- Ventanas temporales relevantes.
- Reglas de acumulación y decaimiento.
- Modelo conceptual de dosis.
- Reglas de inferencia de patrones repetidos.
- Reglas para fatiga probable por BJJ.
- Tratamiento de datos incompletos.
- Valores provisionales claramente marcados.

## Criterios de salida

- A partir de un historial de ejemplo se puede explicar qué carga queda activa.
- Dos revisores pueden llegar a una conclusión similar usando las mismas reglas.
- El sistema no necesita preguntar al usuario si hizo demasiada bisagra, tirón o agarre.
- El modelo distingue entre carga observada, carga estimada e incertidumbre.
- Existen ejemplos de cálculo expresados únicamente como pseudocódigo o reglas funcionales.

## Estado

Pendiente de definición detallada.

---

# Fase 4. Motor de decisión

## Objetivo

Definir la secuencia completa que lleva desde el estado diario hasta una familia de sesión y un presupuesto de carga.

## Decisiones principales

- Detectar restricciones de seguridad.
- Determinar si corresponde descanso, recuperación o entrenamiento.
- Interpretar la posibilidad de BJJ.
- Determinar la intensidad máxima apropiada.
- Seleccionar la familia de sesión.
- Establecer presupuestos por dimensiones.
- Elegir patrones prioritarios y patrones restringidos.

## Entregables

- Cuestionario diario mínimo.
- Reglas duras.
- Reglas de carga.
- Reglas de preferencia.
- Orden de prioridad entre reglas.
- Árboles y flujos en pseudocódigo.
- Matriz de tipos de sesión.
- Explicaciones esperadas para cada decisión.

## Criterios de salida

- Todos los escenarios principales producen una familia de sesión coherente.
- Una motivación alta no puede anular una restricción.
- La ausencia de BJJ no obliga a seleccionar una sesión potente.
- La disponibilidad incierta de BJJ conserva margen.
- El resultado incluye una explicación comprensible.
- Los conflictos entre reglas tienen una prioridad definida.

## Estado

Diseño inicial existente; falta formalización completa.

---

# Fase 5. Generador de sesiones

## Objetivo

Definir cómo se construye una sesión concreta una vez seleccionados el tipo de sesión, los patrones y el presupuesto de carga.

## Decisiones principales

- Número de bloques.
- Orden de ejercicios.
- Selección entre fuerza, técnica, potencia, acondicionamiento y movilidad.
- Cantidad de ejercicios.
- Volumen e intensidad.
- Descansos.
- Duración.
- Sustituciones.
- Validación del coste combinado.

## Entregables

- Plantillas de sesión por familia.
- Reglas de composición.
- Reglas de dosificación.
- Reglas de sustitución.
- Validación final de la sesión.
- Casos de ejemplo completos.

## Criterios de salida

- Se pueden generar sesiones completas para los escenarios A, B, C y D.
- Las sesiones respetan el presupuesto total y los presupuestos locales.
- No se repiten patrones de forma accidental.
- El usuario puede sustituir un ejercicio sin invalidar el objetivo de la sesión.
- La duración se adapta al tiempo disponible.
- Cada sesión explica por qué contiene esos bloques.

## Estado

Pendiente.

---

# Fase 6. Casos de uso y validación manual

## Objetivo

Comprobar el diseño antes de construir software.

## Método

Simular días y semanas reales utilizando únicamente documentación, pseudocódigo, biblioteca e historial ficticio o real anonimizado.

## Entregables

- Casos de uso representativos.
- Casos límite.
- Semanas simuladas.
- Casos con datos incompletos.
- Casos con dolor o limitación.
- Casos con cambios de planes.
- Casos con propuesta rechazada o modificada.
- Registro de incoherencias encontradas.

## Criterios de salida

- El sistema resuelve de forma razonable una muestra amplia de escenarios.
- No aparecen preguntas que el historial debería poder responder.
- Las recomendaciones son explicables.
- Las reglas no producen ciclos o contradicciones frecuentes.
- Se conocen las decisiones aún provisionales.
- Existe un conjunto de casos que luego podrá convertirse en pruebas funcionales.

## Estado

Pendiente.

---

# Puerta de entrada a la aplicación

La aplicación no debe empezar antes de que las fases 1 a 6 estén suficientemente cerradas.

No se exige perfección matemática, pero sí:

- Modelo de dominio estable.
- Biblioteca inicial utilizable.
- Cuestionario diario definido.
- Reglas de decisión coherentes.
- Plantillas de sesión definidas.
- Casos de uso validados manualmente.
- Decisiones provisionales identificadas.
- Alcance del MVP acordado.

Cuando estos criterios se cumplan, el riesgo principal deja de ser diseñar el producto equivocado y pasa a ser implementar correctamente el producto diseñado.

---

# Fase 7. Diseño del MVP

## Objetivo

Definir la primera aplicación útil, sin intentar incluir toda la visión futura.

## Funcionalidades del MVP

### Perfil

- Consultar y editar datos básicos.
- Registrar objetivos y prioridades.
- Registrar material disponible.
- Registrar restricciones permanentes o temporales.

### Estado diario

- Dolor y zona.
- Limitación de movimiento.
- Recuperación percibida.
- Sueño percibido.
- Tiempo disponible.
- Posibilidad e intensidad prevista de BJJ.
- Preferencia opcional.

### Historial

- Registrar BJJ.
- Registrar sesión física.
- Registrar ejercicios, dosis y RPE real.
- Registrar cambios respecto a la propuesta.
- Consultar sesiones recientes.

### Recomendación

- Seleccionar familia de sesión.
- Generar una propuesta.
- Mostrar motivos.
- Mostrar restricciones aplicadas.
- Permitir sustituciones compatibles.
- Permitir reducir duración o carga.

### Seguimiento

- Registrar sensación al terminar.
- Registrar molestias posteriores.
- Registrar estado al día siguiente.

## Fuera del MVP

- Integraciones con relojes.
- Aprendizaje automático.
- Recomendaciones nutricionales completas.
- Red social.
- Marketplace de rutinas.
- Gestión de múltiples entrenadores.
- Diagnóstico de lesiones.
- Automatización avanzada sin supervisión.

## Criterios de salida

- Existe una definición cerrada de pantallas y flujos.
- Cada funcionalidad se relaciona con un requisito del dominio.
- Está claro qué información se introduce y qué se deriva.
- Se ha elegido qué parte del algoritmo entra en la primera versión.
- Se han definido criterios de aceptación funcionales.

## Estado

Pendiente.

---

# Fase 8. Construcción de la aplicación MVP

## Objetivo

Implementar el MVP definido en la fase anterior.

La elección entre React, Svelte u otra tecnología pertenece a esta fase y no debe alterar el modelo funcional.

## Resultado esperado

Una aplicación local o desplegable que permita completar el ciclo:

```text
Declarar estado diario
→ recibir propuesta
→ modificar o aceptar
→ registrar sesión real
→ registrar respuesta posterior
→ conservar historial
```

## Criterios de salida

- El flujo principal funciona de extremo a extremo.
- Los casos de prueba funcionales principales pasan.
- Las decisiones del motor son trazables.
- Los datos pueden exportarse.
- El usuario puede corregir registros.
- La aplicación no oculta incertidumbre ni inventa datos.

## Estado

No iniciada.

---

# Fase 9. Uso personal y calibración

## Objetivo

Utilizar el MVP durante un periodo suficiente para descubrir diferencias entre el modelo teórico y la respuesta real.

## Funcionalidades o actividades

- Comparar propuesta y sesión realizada.
- Detectar sustituciones frecuentes.
- Revisar recomendaciones rechazadas.
- Analizar molestias posteriores.
- Ajustar costes individuales.
- Revisar la utilidad del cuestionario diario.
- Detectar campos que generan fricción y no aportan valor.

## Criterios de salida

- Existe un volumen mínimo de historial real.
- Se han identificado errores sistemáticos.
- Se han ajustado los costes más relevantes.
- El sistema produce recomendaciones útiles con una frecuencia aceptable.
- Se conocen las funciones necesarias para la siguiente versión.

## Estado

No iniciada.

---

# Fase 10. Producto personal completo

## Objetivo

Convertir el MVP calibrado en una herramienta personal madura.

## Funcionalidades previstas

- Panel de carga por dimensiones.
- Vista semanal y mensual.
- Evolución de fuerza y capacidad.
- Alertas de acumulación.
- Gestión de progresiones.
- Semanas de descarga.
- Planificación flexible de objetivos.
- Biblioteca editable.
- Importación y exportación.
- Explicaciones históricas de las decisiones.
- Comparación entre carga prevista y respuesta real.

## Criterios de salida

- El usuario puede utilizar el sistema como herramienta habitual.
- El historial aporta decisiones mejores que una recomendación genérica.
- Las reglas pueden modificarse sin reescribir toda la aplicación.
- La biblioteca puede crecer manteniendo consistencia.

## Estado

No iniciada.

---

# Fase 11. Integraciones opcionales

## Objetivo

Reducir entrada manual y añadir contexto, sin convertir datos imperfectos en verdades absolutas.

## Integraciones posibles

- Frecuencia cardiaca y reposo.
- Sueño del wearable.
- Pasos.
- Calendario.
- Registro de peso.
- Exportación a formatos abiertos.
- Importación desde otras aplicaciones.

## Condiciones

- Toda integración debe ser opcional.
- El usuario debe poder corregir el dato.
- El sistema debe distinguir dato medido, declarado y estimado.
- Ningún wearable debe invalidar automáticamente una sensación subjetiva intensa.

## Estado

No iniciada.

---

# Fase 12. Adaptación avanzada

## Objetivo

Personalizar progresivamente costes, tiempos de recuperación y recomendaciones.

## Capacidades posibles

- Ajustar el coste individual de ejercicios y combinaciones.
- Detectar patrones asociados a molestias.
- Estimar recuperación habitual por tipo de sesión.
- Recomendar progresiones según rendimiento real.
- Detectar infraentrenamiento o estancamiento.
- Mejorar la selección entre varias sesiones válidas.

## Restricción principal

La adaptación avanzada no debe ser una caja negra que impida explicar la recomendación.

## Estado

No iniciada.

---

# Funcionalidades transversales

Estas capacidades afectan a varias fases:

## Explicabilidad

Toda recomendación debe poder mostrar:

- Datos relevantes utilizados.
- Inferencias realizadas.
- Reglas aplicadas.
- Motivos de exclusión.
- Nivel de incertidumbre.

## Corrección

El usuario debe poder corregir:

- Sesiones registradas.
- Intensidad.
- Ejercicios.
- RPE.
- Dolor o respuesta posterior.

## Portabilidad

Los datos deben poder exportarse en un formato comprensible y reutilizable.

## Seguridad funcional

El sistema debe favorecer decisiones conservadoras cuando:

- Falten datos importantes.
- Exista dolor relevante.
- Exista limitación de movimiento.
- El historial muestre respuestas negativas repetidas.

---

# Próximos objetivos concretos

El orden inmediato recomendado es:

1. Cerrar el glosario y modelo de dominio.
2. Completar la taxonomía de patrones y dimensiones de carga.
3. Ampliar la biblioteca de ejercicios y variantes.
4. Diseñar el modelo de carga y decaimiento.
5. Cerrar el cuestionario diario mínimo.
6. Formalizar las reglas del motor de decisión.
7. Definir las plantillas del generador de sesiones.
8. Construir casos de uso y validarlos manualmente.
9. Definir el alcance del MVP.
10. Solo entonces seleccionar arquitectura y comenzar la aplicación.

## Próximo hito

**Modelo funcional validable**.

Se alcanza cuando, usando únicamente documentos, biblioteca, historial de ejemplo y pseudocódigo, puede generarse y justificar una sesión para los escenarios principales sin decisiones improvisadas por quien lo ejecuta.
