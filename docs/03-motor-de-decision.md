# Motor de decisión diario

## Propósito

Definir la secuencia completa que lleva del estado diario a una familia de sesión y un presupuesto de carga por dimensiones. Corresponde a la Fase 4 del roadmap (`docs/10`).

La generación de la sesión concreta (bloques, ejercicios, dosis) es responsabilidad del generador (Fase 5, `docs/06`).

## Cuestionario diario mínimo

Inputs definitivos. Los cuatro primeros son obligatorios (`docs/11`); el resto es opcional.

- `recuperacion`: verde, amarillo o rojo (semáforo de `docs/04`).
- `dolor`: 0-10. Si es mayor que 0, `zona_dolor`.
- `bjj_disponible`: si, no o incierto.
- `tipo_bjj`: tecnico, normal o duro (solo si `bjj_disponible` es si; si se desconoce, se asume normal).
- `limitacion`: movimiento restringido, si aplica.
- `tiempo_disponible`: minutos, si el día lo exige.
- `preferencia`: fuerza, potencia, acondicionamiento, técnica o recuperación. Nunca anula una restricción.
- `circunstancias`: enfermedad, viaje, estrés, falta de sueño, si aplica.

El motor no pregunta nada que el historial pueda responder (`docs/09`).

## Reglas

### Reglas duras (D)

Seguridad. No negociables; ninguna otra regla ni la preferencia del usuario puede anularlas.

- **D1**: dolor relevante (≥ 4, provisional) o limitación de movimiento → recuperación activa o descanso.
- **D2**: recuperación roja → recuperación activa o descanso. La motivación no convierte un día rojo en verde.
- **D3**: si hay BJJ normal o duro después, la sesión física no puede incluir ejercicios de `impacto_lumbar` amarillo o rojo.
- **D4**: nunca dos estímulos altos sobre la zona lumbar el mismo día (física + BJJ duro ya cuenta como uno).
- **D5**: nunca dos días consecutivos de bisagra exigente.
- **D6**: ante incertidumbre (datos incompletos), decisión conservadora.

### Reglas de carga (C)

Usan la carga activa por dimensiones calculada según `docs/12`.

- **C1**: dimensión en `alta` → los patrones que la alimentan quedan restringidos (excluidos o en dosis reducida).
- **C2**: dimensión en `media` → los patrones que la alimentan pierden prioridad y se dosifican.
- **C3**: `total` en `alta` → familia C (recuperación) como máximo, salvo que el usuario declare verde y sin dolor, caso en el que se permite familia A reducida.
- **C4**: si ayer hubo doble sesión o BJJ duro → hoy la intensidad máxima es media.
- **C5**: BJJ incierto → se conserva margen como si fuera a ocurrir (tipo normal).
- **C6**: la ausencia de BJJ no obliga a sesión potente; el objetivo del día y la recuperación mandan.

### Reglas de preferencia (P)

Solo se aplican cuando las reglas D y C dejan más de una opción.

- **P1**: un patrón con más de 7 días sin estímulo (provisional) tiene prioridad si el presupuesto lo permite.
- **P2**: la preferencia declarada desempata entre opciones válidas.
- **P3**: `tiempo_disponible` reduce la duración de la sesión sin cambiar su familia, salvo que el tiempo sea insuficiente para el mínimo de la familia.

### Prioridad entre reglas

```text
1. Reglas duras (D)          → deciden si se entrena y con qué techo
2. Reglas de carga (C)       → deciden familia de sesión y presupuesto
3. Reglas de preferencia (P) → desempatan entre opciones válidas
```

Coherente con la prioridad de fuentes de `docs/09`.

## Flujo completo (pseudocódigo)

```text
entrada: estado diario (cuestionario) + historial + biblioteca

1. carga_activa = calcular_carga(historial, biblioteca)     # docs/12
2. # Reglas duras
   si dolor >= 4 o limitacion:        → descanso o familia C; fin  # D1
   si recuperacion == rojo:           → familia C o descanso; fin  # D2
3. # Reglas de carga: techo de intensidad
   techo = potente
   si total alta:                     techo = recuperacion         # C3
   si doble sesión o BJJ duro ayer:   techo = min(techo, media)    # C4
   si recuperacion == amarillo:       techo = min(techo, compatible)
4. # Familia de sesión
   si bjj_disponible == si o incierto:
       si techo >= compatible:        → familia A (compatible BJJ)
       si no:                         → familia C
   si bjj_disponible == no:
       si techo == potente:           → familia B (potente)         # C6 no obliga
       si techo == compatible:        → familia A o D
       si no:                         → familia C
5. # Presupuesto por dimensión
   para cada dimensión:
       presupuesto = umbral_alto - carga_activa                     # C1, C2
       si familia A: presupuesto *= factor_compatible (0.5, provisional)
       presupuesto = max(presupuesto, 0)
6. # Patrones
   restringidos = patrones que alimentan dimensiones en alta        # C1
   prioritarios = patrones con > 7 días sin estímulo                # P1
                 ∩ patrones permitidos por la familia
                 - restringidos
7. # Verificaciones finales
   aplicar D3, D4, D5 sobre la selección preliminar
8. salida: familia, presupuesto por dimensión, patrones prioritarios,
   patrones restringidos, explicación, incertidumbre declarada
```

## Matriz de tipos de sesión

Familia resultante según semáforo, BJJ y carga total (resumen; las reglas del flujo prevalecen):

| Recuperación | BJJ | Carga total | Familia |
|---|---|---|---|
| roja | cualquiera | cualquiera | C o descanso (D2) |
| cualquiera | cualquiera | dolor relevante | C o descanso (D1) |
| amarilla | si/incierto | cualquiera | A reducida |
| amarilla | no | baja/media | A o D |
| amarilla | no | alta | C |
| verde | si (técnico) | baja/media | A |
| verde | si (normal/duro) | baja/media | A (con D3, D4) |
| verde | incierto | baja/media | A (con margen, C5) |
| verde | no | baja/media | B |
| verde | no | alta | A reducida o C (C3) |

La familia D (técnica y agilidad) puede sustituir a A cuando el objetivo del día es técnica, o complementarla como segundo bloque corto.

## Explicación esperada

Toda decisión produce una explicación con este contenido mínimo:

- Familia elegida y por qué (reglas aplicadas, con su código: D1, C3...).
- Restricciones activas (patrones excluidos y su motivo).
- Carga activa relevante por dimensión y su origen (qué sesiones la generaron).
- Incertidumbre: datos estimados o desconocidos y qué asunción conservadora se aplicó.

Ejemplo: «Familia A. Lumbar y bisagra en media por swing + peso muerto de ayer (C2): se excluyen swings y pesos muertos. BJJ normal previsto: se aplican D3 y se deja margen de agarre (C1). Empuje y piernas frescas: patrones prioritarios.»

## Valores provisionales

- Umbral de dolor relevante (D1): 4.
- Factor de presupuesto para familia compatible (paso 5): 0.5.
- Umbral de ausencia de patrón (P1): 7 días.
- Interpretación de BJJ incierto (C5): asumir normal.
