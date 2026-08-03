# Fuentes de datos e inferencias

## Propósito

Definir qué información aporta el usuario, qué información registra el sistema y qué conocimiento debe inferir el motor a partir de la biblioteca y del historial.

El objetivo es que el cuestionario diario sea breve y que el usuario no tenga que interpretar su propia carga de entrenamiento.

## Principio general

```text
Datos declarados por el usuario
+
Datos registrados en sesiones
+
Metadatos de la biblioteca
↓
Variables derivadas
↓
Decisión y explicación de la sesión
```

## Datos declarados

Información que el sistema no puede conocer con fiabilidad:

- Dolor o molestia actual.
- Zona e intensidad de la molestia.
- Limitación de movimiento.
- Sensación de recuperación.
- Fatiga localizada percibida.
- Calidad subjetiva del sueño.
- Tiempo disponible.
- Posibilidad de BJJ.
- Intensidad prevista del BJJ, cuando se conozca.
- Preferencia o motivación del día.
- Circunstancias extraordinarias: enfermedad, viaje, estrés o falta de sueño.

## Datos registrados

### Sesión física

- Fecha y hora.
- Duración.
- Tipo de sesión.
- Ejercicios y variantes.
- Series, repeticiones o tiempo.
- Carga externa.
- Descansos, cuando sean relevantes.
- RPE previsto y real.
- Cambios respecto a la propuesta.
- Molestias durante o después.

### BJJ

- Duración total.
- Tiempo aproximado de técnica.
- Número y duración de rondas.
- Intensidad percibida.
- Clasificación: técnico, normal o duro.
- Fatiga de agarre.
- Molestias o incidencias.

### Respuesta posterior

- Sensación al terminar.
- Molestias posteriores.
- Estado al día siguiente.
- Tiempo necesario para recuperar.

## Información aportada por la biblioteca

Cada ejercicio o variante debe describir:

- Patrón principal y secundarios.
- Material.
- Nivel y dificultad.
- Bilateral o unilateral.
- Dinámico o isométrico.
- Controlado o explosivo.
- Coste base por dimensiones.
- Compatibilidad con BJJ.
- Restricciones.
- Progresiones, regresiones y sustitutos.

Dimensiones de carga previstas:

- Total.
- Lumbar.
- Bisagra de cadera.
- Rodilla y piernas.
- Hombro y codo.
- Agarre.
- Core.
- Cardio.
- Impacto articular.

## Variables derivadas

El motor debe inferir, sin preguntarlas directamente:

- Carga acumulada en 24, 48 y 72 horas.
- Carga lumbar activa.
- Volumen reciente de bisagra.
- Fatiga probable de agarre.
- Carga de empuje, tirón y piernas.
- Carga cardiovascular.
- Tiempo desde el último trabajo de cada patrón.
- Repetición o ausencia de patrones.
- Sesiones exigentes consecutivas.
- Dobles sesiones recientes.
- Compatibilidad con una segunda sesión.
- Presupuesto disponible por dimensiones.
- Necesidad probable de recuperación o descarga.
- Incertidumbre causada por datos incompletos.

## Dosis e impacto real

El coste de un ejercicio no es fijo. Debe ajustarse conceptualmente según:

```text
impacto estimado = coste base
                   ajustado por volumen
                   ajustado por intensidad relativa
                   ajustado por carga externa
                   ajustado por proximidad al fallo
                   ajustado por velocidad y densidad
                   ajustado por fatiga previa
                   ajustado por respuesta individual conocida
```

Este bloque es pseudocódigo conceptual, no una fórmula definitiva.

## Ejemplo: exceso reciente de bisagra

Historial:

- Swing a una mano.
- Peso muerto maleta.
- Remo inclinado.
- BJJ normal o duro el mismo día.

La biblioteca relaciona esos elementos con bisagra, zona lumbar, cadena posterior, agarre y antirrotación.

Resultado derivado:

```text
carga_bisagra_48h = alta
carga_lumbar_48h = alta
carga_agarre_48h = media_alta
```

Consecuencia funcional:

- Reducir o excluir temporalmente ejercicios de alto coste lumbar.
- Disminuir prioridad de swings, windmills y pesos muertos.
- Favorecer patrones compatibles con la carga restante.

El usuario no debe declarar «ayer hice demasiada bisagra».

## Prioridad entre fuentes

1. Dolor, limitación o síntoma actual.
2. Restricciones de seguridad.
3. Respuesta negativa registrada anteriormente.
4. Carga inferida desde historial y biblioteca.
5. Objetivos de progresión.
6. Preferencia y motivación.

La percepción actual del usuario prevalece sobre una estimación optimista del historial.

## Datos que no deben preguntarse

Salvo ausencia total de historial, no se debe preguntar al usuario:

- Si hizo demasiada bisagra.
- Si acumula demasiado tirón o agarre.
- Si falta empuje o pierna en la semana.
- Si encadenó demasiadas sesiones duras.
- Si necesita una descarga.
- Si una propuesta supera el presupuesto lumbar.

## Incertidumbre

El sistema debe distinguir entre:

- Dato conocido.
- Dato estimado.
- Dato desconocido.

Cuando falten datos debe actuar de forma conservadora, explicar la incertidumbre y pedir únicamente información que el usuario pueda aportar directamente.
