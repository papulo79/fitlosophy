# Biblioteca de ejercicios

La fuente de verdad estructurada es `data/ejercicios.yaml`. Este documento explica su organización.

## Taxonomía de patrones

Lista cerrada de patrones de movimiento. Todo ejercicio del catálogo usa uno de estos valores como patrón principal; añadir un patrón nuevo exige actualizar primero esta lista y la sección `valores` de `data/ejercicios.yaml`.

### Empuje

- `empuje_horizontal`: empujar la carga alejándola del torso en plano horizontal (flexiones, press de banca). Alimenta hombro y empuje.
- `empuje_vertical`: empujar la carga por encima de la cabeza (press militar, press con mancuernas). Alimenta hombro y empuje.

### Tirón

- `tiron_horizontal`: tracción hacia el torso en plano horizontal (remos). Alimenta tirón, agarre y hombro.
- `tiron_vertical`: tracción en plano vertical (dominadas, jalones). Alimenta tirón, agarre y hombro.

### Pierna

- `dominante_rodilla`: la rodilla es la articulación principal del gesto (sentadillas, zancadas, pistol). Alimenta rodilla y piernas.
- `dominante_cadera`: bisagra de cadera con cadena posterior como protagonista (peso muerto, swing, puente de glúteos). Alimenta bisagra y lumbar.

### Core

- `core_antiextension`: resistir la extensión lumbar (plancha frontal, dead bug). Alimenta core y lumbar.
- `core_antirotacion`: resistir la rotación del tronco (pallof press, remos unilaterales con apoyo). Alimenta core.
- `core_lateral`: resistir la flexión lateral (plancha lateral, carries). Alimenta core.
- `core_flexion_cadera`: flexión activa de cadera con tronco estable (elevaciones colgado). Alimenta core y agarre.
- `core_rotacion`: rotación cargada del tronco (russian twist). Por defecto es un patrón de riesgo lumbar alto en este perfil; se dosifica con criterio conservador.

### Locomoción

- `acondicionamiento`: trabajo cíclico cardiovascular (comba, circuitos, intervalos). Alimenta cardio e impacto articular.
- `agilidad`: cambios de dirección y coordinación de apoyos (escalera, conos, desplazamientos). Alimenta cardio, impacto articular y, en zigzag, rodilla.

### Movilidad y recuperación

- `movilidad_cargada`: movilidad con carga externa (windmill). Alimenta lumbar y hombro; siempre requiere dosificación.
- `recuperacion`: movimiento regenerativo de baja intensidad (caminata, movilidad suave, respiración). No genera carga relevante en ninguna dimensión.

### Criterio de asignación

1. El patrón principal es el que determina el objetivo del ejercicio en la sesión, no necesariamente el de mayor demanda física.
2. Si un ejercicio exige de forma relevante un segundo patrón, se declara en `secundarios` (ej. swing a una mano: `dominante_cadera` + `core_antirotacion`).
3. Un ejercicio tiene un único patrón principal; si parece tener dos, la variante más específica suele resolver la duda.
4. Ante la duda entre dos patrones, se asigna el que el motor necesita para proteger al usuario (ej. un gesto de bisagra con rotación se clasifica por la bisagra y la rotación queda en `secundarios`).

## Etiquetas

Cada ejercicio define:

- Patrón de movimiento principal (de la taxonomía).
- Patrones secundarios, cuando aplica.
- Material necesario.
- Nivel (`base`, `intermedio`, `avanzado`) y lateralidad (`bilateral`, `unilateral`).
- Flags opcionales: `explosivo`, `isometrico`, `sin_material` (ejecutable sin ningún material; el tatami cuenta como suelo).
- Objetivos.
- Coste por dimensión de carga (`coste_dimensiones`, niveles bajo/medio/alto por dimensión de `docs/12`).
- Impacto lumbar estimado.
- Compatibilidad con BJJ posterior.
- Progresiones, regresiones y sustitutos (referencias a otros `id` del catálogo).
- Rango orientativo de series y repeticiones.
- Descripción de ejecución y, cuando la dosis lo exige, la lista de patrones a recorrer (ver la sección siguiente).

## Ejecución

Las etiquetas anteriores sirven al motor para decidir; no le dicen nada al usuario sobre **cómo** se hace el ejercicio. Para eso, cada ejercicio lleva:

- `descripcion` (obligatorio): una o dos frases con la ejecución y la clave técnica que más importa en este perfil. Es lo que se muestra bajo la dosis en la propuesta y en la ejecución. Se escribe en imperativo y en español, sin repetir el nombre del ejercicio.
- `patrones` (opcional): lista ordenada de las variantes concretas que se recorren dentro del ejercicio.

Criterios:

1. La descripción declara la restricción de seguridad cuando existe. Si el ejercicio tiene `impacto_lumbar: rojo` o algún flag de técnica (`detener_si_falla_tecnica`, `sin_balanceo`, `evitar_fallo`), su descripción lo dice con palabras, no solo con la etiqueta.
2. La descripción no repite la dosis: las series y repeticiones ya salen de `prescripcion`, y duplicarlas las desincronizaría.
3. **`patrones` es obligatorio cuando la prescripción se expresa por patrón** (hoy, `pasadas_por_patron`). Sin esa lista la dosis es incompleta: «4 pasadas» no dice de qué, y el usuario no puede ejecutar la sesión. Un test del catálogo lo verifica.
4. La descripción explica *qué* hacer, no *por qué* está hoy en la sesión: el motivo lo genera el motor en la justificación del ítem (`docs/03`).

## Intención del ejercicio

La biblioteca no prescribe kilos: el peso externo depende del estado del día y de la fuerza del momento, y el modelo de carga de `docs/12` es ciego a la intensidad (el coste por dimensión es un nivel fijo del ejercicio, no una función del peso). Prescribir un número exigiría un dato de fuerza por ejercicio que el perfil no tiene.

En su lugar se declara **con qué intención** se hace el ejercicio, y el atleta elige el peso. La intención se deriva del **primer elemento de `objetivos`**, que el catálogo lista por orden de importancia, y se reduce a un vocabulario cerrado:

| Intención | Origen (`objetivos[0]`) | Qué le dice al atleta |
|---|---|---|
| `fuerza` | `fuerza`, `fuerza_unilateral` | Pocas repeticiones y peso alto para el rango |
| `potencia` | `potencia` | Velocidad; el peso no debe frenar el gesto |
| `resistencia` | `fuerza_resistencia`, `volumen` | Muchas repeticiones y peso sostenible |
| `control` | `tecnica`, `estabilidad_*`, `core`, `rotacion`, `activacion` | La calidad manda; el peso es secundario |
| `coordinacion` | `coordinacion` | Cadencia y apoyos limpios antes que intensidad |
| `movilidad` | `movilidad` | Recorrido y control, carga mínima |
| `cardio` | `cambio_direccion`, `aceleracion`, `acondicionamiento`, `cardio` | Continuidad y ritmo |
| `recuperacion` | `recuperacion`, `recuperacion_activa` | Sin buscar estímulo |

Junto a la intención se muestra la **reserva de repeticiones de la familia** (`docs/06`), que es la instrucción concreta para elegir el peso: en familia B, «deja 1-3 repeticiones en recámara» acota la carga sin necesidad de un número.

La reserva solo se muestra donde significa algo: en ejercicios dosificados en **repeticiones**. No aplica a los isométricos ni a los que se dosifican en segundos, minutos, saltos o pasadas —«deja 1-3 repeticiones en recámara» no dice nada en una plancha de 32 s—, ni a B0 y B4, que por la regla 8 de `docs/06` no buscan estímulo.

El peso realmente usado se registra en `carga_kg_real`. Hoy no alimenta el modelo de carga; se acumula para poder sugerir progresión más adelante (`docs/07`: una sola variable a la vez, y solo si se cerró el rango alto con el RPE previsto o menor).

## Criterio lumbar

- `verde`: uso habitual y baja demanda lumbopélvica.
- `amarillo`: requiere dosificación o buena técnica.
- `rojo`: alto coste lumbar para este perfil; reservar normalmente para días sin BJJ.

Una etiqueta roja no significa que el ejercicio sea malo o peligroso de forma universal.

## Material disponible

- TRX.
- Tatami.
- Barra de dominadas.
- Kettlebells de 8, 12 y 16 kg.
- Comba.
- Caja.
- Gomas.
- Conos.
- Escalera de agilidad.
- Cinta de caminar/correr hasta 12 km/h.
