# Motor de decisión diario

## Inputs

- `bjj_disponible`: sí, no o incierto.
- `tipo_bjj`: técnico, normal o duro.
- `recuperacion`: verde, amarillo o rojo.
- `dolor`: 0-10 y zona afectada.
- `carga_48h`: baja, media o alta.
- `objetivo_dia`: fuerza, potencia, acondicionamiento, técnica o recuperación.

## Orden de decisión

1. Estado de la espalda y articulaciones.
2. Fatiga acumulada en las últimas 48-72 horas.
3. Posibilidad y dureza prevista del BJJ.
4. Objetivo físico del día.
5. Preferencia personal y motivación.

## Árbol inicial

```text
¿Hay dolor relevante o limitación de movimiento?
├── Sí → recuperación activa o descanso
└── No
    ├── ¿Recuperación roja o carga alta?
    │   └── recuperación activa
    ├── ¿Puede haber BJJ?
    │   ├── Sí → físico compatible con BJJ
    │   ├── Incierto → físico compatible y reevaluación
    │   └── No → físico potente
```

## Reglas iniciales

- No programar una sesión física de alto coste lumbar antes de BJJ normal o duro.
- Si el BJJ es incierto, conservar margen.
- Un día amarillo puede entrenarse, pero se reduce volumen o dificultad.
- Un día rojo no se convierte en verde por motivación.
- La ausencia de BJJ no obliga a realizar una sesión potente.
