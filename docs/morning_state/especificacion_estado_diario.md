# Especificación funcional — Estado diario

**Versión:** 1.0  
**Módulo:** Estado diario  
**Tipo:** Registro matutino de bienestar y recuperación  
**Alcance:** Funcional, sin decisiones sobre modelos de datos ni implementación técnica.

## 1. Objetivo

Incorporar a la aplicación un apartado independiente de los entrenamientos, denominado **Estado diario**, que se rellene **una sola vez por la mañana**.

Debe permitir valorar dos cuestiones:

- **¿Cómo me ha afectado lo que hice ayer?** Descanso, recuperación y molestias.
- **¿En qué condiciones estoy para afrontar hoy?** Energía física, claridad mental y exigencia mental prevista.

El registro debe poder completarse en aproximadamente **20–30 segundos**, sin escribir texto. Debe funcionar también los días sin entrenamiento.

En la primera versión se utilizará para registrar y consultar tendencias. **No modificará automáticamente los entrenamientos.**

## 2. Indicadores y escalas

Se registran **seis indicadores** en una única pantalla, en este orden:

| Orden | Nombre visible | Pregunta | Valores |
|---|---|---|---|
| 1 | Calidad del sueño | ¿Cómo has dormido? | 1–5 |
| 2 | Recuperación física | ¿Cómo notas tu recuperación? | 1–5 |
| 3 | Molestias físicas | ¿Tienes dolor o molestias? | 0–10 |
| 4 | Energía física | ¿Cómo te encuentras físicamente? | 1–5 |
| 5 | Claridad mental | ¿Cómo te encuentras mentalmente? | 1–5 |
| 6 | Estrés previsto | ¿Qué exigencia mental esperas hoy? | 1–5 |

### 2.1. Calidad del sueño

| Valor | Etiqueta |
|---|---|
| 1 | Muy mal |
| 2 | Mal |
| 3 | Regular |
| 4 | Bien |
| 5 | Muy bien |

Evalúa el descanso **percibido**, no únicamente las horas dormidas.

### 2.2. Recuperación física

| Valor | Etiqueta |
|---|---|
| 1 | Muy fatigado |
| 2 | Fatigado |
| 3 | Algo cansado |
| 4 | Recuperado |
| 5 | Totalmente recuperado |

Evalúa la fatiga corporal y muscular acumulada, incluso si no se entrenó el día anterior.

### 2.3. Molestias físicas

| Valor | Interpretación |
|---|---|
| 0 | Sin molestias |
| 1–3 | Molestias leves |
| 4–6 | Molestias moderadas |
| 7–10 | Molestias intensas |

Si el valor es superior a 0, mostrar el campo **¿Dónde tienes molestias?**, de selección múltiple y opcional, con las opciones:

- Lumbar
- Cervical
- Hombros
- Brazos/manos
- Cadera
- Rodillas
- Piernas/pies
- Otras

### 2.4. Energía física

| Valor | Etiqueta |
|---|---|
| 1 | Agotado |
| 2 | Poca energía |
| 3 | Normal |
| 4 | Con energía |
| 5 | Excelente |

Diferenciar **energía física** de **recuperación**: es posible estar muscularmente recuperado y sentirse sin energía.

### 2.5. Claridad mental

| Valor | Etiqueta |
|---|---|
| 1 | Muy espeso |
| 2 | Poco despejado |
| 3 | Normal |
| 4 | Despejado |
| 5 | Muy despejado |

Evalúa concentración y claridad mental percibidas antes de empezar la jornada profesional.

### 2.6. Estrés previsto

| Valor | Etiqueta |
|---|---|
| 1 | Muy baja |
| 2 | Baja |
| 3 | Normal |
| 4 | Alta |
| 5 | Muy alta |

Se refiere a la **exigencia mental esperada para el día**. A diferencia de las escalas de bienestar, un valor alto no significa un mejor estado.

## 3. Comportamiento funcional

- Se permitirá **un registro por fecha**, asociado automáticamente al día correspondiente.
- El registro se realizará **por la mañana**, en **una sola pantalla**.
- Cada indicador será **opcional individualmente**; se podrán guardar registros parciales.
- Se priorizarán controles de selección rápidos, **sin necesidad de introducir texto**.
- No se copiarán automáticamente las valoraciones de días anteriores.
- Se podrán consultar y modificar registros anteriores.
- Se podrá registrar el estado tanto en días de entrenamiento como en días de descanso.
- Habrá un campo opcional **Observaciones**, de texto libre, reservado para circunstancias excepcionales. No será necesario rellenarlo habitualmente.

## 4. Consulta e histórico

El módulo permitirá:

- Consultar los valores de cada día.
- Revisar una **vista semanal** con los últimos siete días.
- Visualizar tendencias para períodos de **7, 14 y 30 días**.
- Distinguir expresamente los **días sin registro** de los días con puntuaciones bajas.

Los seis indicadores se analizarán **por separado**. No se calculará en la versión 1.0 una puntuación global de recuperación ni se aplicarán ponderaciones arbitrarias.

## 5. Relación futura con entrenamientos

En la versión 1.0, el módulo será **informativo**: no cambiará rutinas ni decidirá cargas automáticamente.

Más adelante, los datos podrán ayudar a:

- Detectar fatiga acumulada y cambios de recuperación.
- Relacionar el estado matutino con la carga deportiva de días anteriores.
- Identificar patrones entre sueño, claridad mental y entrenamiento.
- Considerar molestias y exigencia mental prevista al proponer actividad.

Estas decisiones requerirán reglas que se definan y contrasten posteriormente; no forman parte del alcance actual.

## 6. Requisitos funcionales

| ID | Requisito | Prioridad |
|---|---|---|
| ED-01 | Incorporar apartado independiente «Estado diario» | Alta |
| ED-02 | Permitir un registro matutino por fecha | Alta |
| ED-03 | Registrar calidad del sueño (1–5) | Alta |
| ED-04 | Registrar recuperación física (1–5) | Alta |
| ED-05 | Registrar molestias físicas (0–10) | Alta |
| ED-06 | Permitir indicar localización opcional de molestias | Media |
| ED-07 | Registrar energía física (1–5) | Alta |
| ED-08 | Registrar claridad mental (1–5) | Alta |
| ED-09 | Registrar estrés previsto (1–5) | Alta |
| ED-10 | Permitir observaciones opcionales | Baja |
| ED-11 | Guardar registros parciales y editar registros anteriores | Alta |
| ED-12 | Consultar histórico por día | Alta |
| ED-13 | Mostrar tendencias de 7, 14 y 30 días | Media |
| ED-14 | Comparar bienestar con entrenamientos | Futura |
| ED-15 | Adaptar recomendaciones de entrenamiento | Futura |

## 7. Criterios de aceptación

La primera versión se considerará completa cuando:

1. Los seis indicadores puedan valorarse en una sola pantalla en aproximadamente 20–30 segundos.
2. Se pueda completar el registro sin escribir texto.
3. Las escalas y etiquetas sean consistentes entre días.
4. Las molestias permitan seleccionar opcionalmente una o varias localizaciones.
5. Se puedan guardar registros parciales, consultar el histórico y editar días anteriores.
6. El registro funcione independientemente de si se entrenó o no.
7. Se puedan consultar tendencias sin crear índices globales.
8. El registro no provoque modificaciones automáticas de la planificación deportiva.

## 8. Fuera del alcance de la versión 1.0

No incluir en este formulario matutino:

- Peso, grasa corporal u otras medidas de composición corporal.
- Pasos, frecuencia cardíaca o calorías.
- Alimentación y comidas.
- Registro de ejercicios o sesiones deportivas.
- Formularios nocturnos o un segundo registro diario obligatorio.
- Índices automáticos de recuperación o decisiones automáticas de entrenamiento.

Estos datos, si se utilizan en el futuro, pertenecerán a sus propios apartados o integraciones y no deberán complicar el registro matutino.
