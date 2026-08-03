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
- Objetivos.
- Coste de fatiga.
- Impacto lumbar estimado.
- Compatibilidad con BJJ posterior.
- Rango orientativo de series y repeticiones.
- Observaciones y regresiones.

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
