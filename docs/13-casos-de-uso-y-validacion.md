# Casos de uso y validación manual

## Propósito

Comprobar el diseño completo antes de construir software (Fase 6 del roadmap, `docs/10`). Cada caso se ejecuta a mano usando únicamente los documentos, la biblioteca (`data/ejercicios.yaml`) y el pseudocódigo de `docs/03`, `docs/06` y `docs/12`.

Estos casos son el material que la Fase 7/8 convertirá en pruebas funcionales del MVP.

## Convenciones de los casos

- Puntos de coste: bajo = 1, medio = 2, alto = 3; secundarios a la mitad (`docs/12`).
- Decaimiento: 24 h ×1.0, 48 h ×0.6, 72 h ×0.3.
- Presupuesto: (8 − carga activa), ×0.5 en familia A, mínimo 0 (`docs/03`).
- Umbral de niveles: < 4 baja, 4-8 media, > 8 alta.

---

## Caso 1. Día verde sin BJJ, historial ligero → familia B

**Historial** (hace 60 h, ventana 48-72 h, ×0.3): sesión A con flexión clásica (empuje 1, core 1), goblet squat (rodilla 2, core 1), pallof press (core 1).

**Carga activa**: empuje 0.3, rodilla 0.6, core 0.9 → todo `baja`.

**Estado diario**: recuperación verde, dolor 0, BJJ no, preferencia fuerza.

**Motor**: sin reglas duras activas; techo potente; sin BJJ → **familia B** (C6 no obliga, pero la preferencia y la recuperación la avalan).

**Presupuestos**: empuje 7.7, tirón 8, agarre 8, bisagra 8, lumbar 8, rodilla 7.4, core 7.1, cardio 8.

**Sesión generada**:

```text
B0: dead bug 2×6 + escalera de agilidad (no computa)
B1: swing a dos manos 6×10     (bisagra 3, lumbar 2, agarre 2, cardio 2)
    press militar KB 4×6/lado  (empuje 2, core 0.5)
    dominada estricta 12 total (tirón 2, agarre 2)
B2: plancha lateral 3×30 s     (core 1)
B3: comba 5×100                (cardio 1, impacto 1)
```

**Validación**: bisagra 3, lumbar 2, agarre 4, empuje 2, tirón 2, core 1.5, cardio 3, impacto 1 → todos dentro de presupuesto. D4: un solo estímulo lumbar (swing, amarillo) ✓. D5: sin bisagra el día anterior ✓. Ningún patrón repetido ✓. Explosivos primero ✓.

**Resultado**: correcto. Sesión potente completa sin violaciones.

---

## Caso 2. BJJ normal por la tarde con lumbar, bisagra y agarre cargados → familia A

Caso desarrollado en `docs/06` (ejemplo completo). Resultado: familia A con empuje y pierna como patrones frescos, core dosificado, agarre en el límite (presupuesto 0): dominadas rechazadas y tirón declarado patrón pendiente.

**Resultado**: correcto. El usuario no declara nada sobre bisagra ni agarre; el sistema lo infiere del historial.

---

## Caso 3. Dolor lumbar al despertar → descanso/recuperación (D1)

**Estado diario**: recuperación amarilla, dolor 5 zona lumbar, BJJ normal previsto por la tarde.

**Motor**: dolor ≥ 4 → **D1**: recuperación activa o descanso. La existencia de BJJ no cambia nada: no hay sesión física que proteger.

**Propuesta**: caminata en cinta 25-30 min + movilidad suave + dead bug 2×6. Nota visible: no usar analgésicos para forzar la sesión (`docs/04`). Recomendación de valorar reducir el BJJ a técnico o ausentarse, con la decisión en manos del usuario.

**Explicación**: «Dolor lumbar 5/10: regla dura D1. Solo recuperación. El BJJ de esta tarde no recibe estímulo previo; si el dolor persiste al mediodía, considera no entrenar.»

**Resultado**: correcto. La regla de seguridad domina sobre agenda y preferencias.

---

## Caso 4. BJJ incierto → familia A con margen (C5)

**Historial** (hace 30 h, ×0.6): BJJ duro (agarre 3, core 3, cardio 3, lumbar 2, impacto 2, bisagra 1).

**Carga activa**: agarre 1.8, core 1.8, cardio 1.8, lumbar 1.2, impacto 1.2, bisagra 0.6 → todo `baja`.

**Estado diario**: verde, dolor 0, BJJ incierto.

**Motor**: C5 → se asume BJJ normal → **familia A**. Techo real: potente, pero el margen se conserva.

**Presupuestos (×0.5)**: agarre 3.1, core 3.1, cardio 3.1, lumbar 3.4, empuje 4, rodilla 4, bisagra 3.7.

**Sesión**: B1: flexión clásica 3×12 (empuje 0.5, core 0.5), búlgara TRX 3×8/lado (rodilla 2, agarre 0.5). B2: plancha frontal 2×30 s (core 0.5). Validación: todo dentro.

**Reevaluación**: si el BJJ finalmente no ocurre, el usuario puede ampliar a familia D (técnica) o añadir B3 suave; no se reconvierte a familia B completa porque la sesión ya se ejecutó con margen.

**Resultado**: correcto. La incertidumbre de agenda produce margen, no parálisis.

---

## Caso 5. Día rojo con motivación alta → la motivación no anula (D2)

**Estado diario**: recuperación roja (5 h de sueño, fatiga alta), dolor 0, sin BJJ, preferencia declarada: «entrenar duro».

**Motor**: **D2** → recuperación activa o descanso. P2 no llega a aplicarse: las reglas de preferencia solo desempatan entre opciones válidas y aquí no hay ninguna sesión de estímulo válida.

**Propuesta**: descanso completo o caminata 20-30 min + respiración. La explicación declara: «Preferencia registrada. La recuperación roja es una regla dura (D2): hoy no hay sesión de estímulo. Si mañana amanece en verde, la sesión potente tendrá prioridad de patrones frescos.»

**Resultado**: correcto. El sistema protege la continuidad frente a la motivación puntual.

---

## Caso 6. Día después de doble sesión (familia B + BJJ duro) → techo medio (C4, C3, D5)

**Historial** (ayer, ×1.0): la sesión B del caso 1 (agarre 4, bisagra 3, cardio 3, lumbar 2, empuje 2, tirón 2, core 1.5, impacto 1) + BJJ duro (agarre 3, core 3, cardio 3, lumbar 2, impacto 2, bisagra 1).

**Carga activa**: agarre 7 (`media`), cardio 6 (`media`), core 4.5 (`media`), lumbar 4 (`media`), bisagra 4 (`media`), impacto 3, empuje 2, tirón 2.

**Nivel total**: 5 dimensiones en media → **total alta** (regla de `docs/12`).

**Estado diario**: verde, dolor 0, sin BJJ.

**Motor**: C4 (doble sesión ayer → techo medio) + C3 (total alta → C como máximo, pero verde sin dolor permite A reducida) → **familia A reducida**. D5: ayer hubo swing (bisagra exigente) → hoy prohibido el trabajo de bisagra exigente.

**Presupuestos (×0.5)**: agarre 0.5, cardio 1, core 1.75, lumbar 2, bisagra 2, empuje 3, rodilla 4, tirón 3.

**Sesión**: B1: flexión en pica 3×8 (empuje 2, core 0.5), goblet squat 3×10 (rodilla 2, core 0.5). B2: plancha lateral 2×25 s (core 0.5). Validación: core 1.5 ≤ 1.75 ✓, agarre 0 ✓, todo dentro.

**Explicación**: «Doble sesión ayer (física + BJJ duro): cinco dimensiones en media, total alta (C3, C4). Sesión reducida sin bisagra (D5) ni agarre (C1). Empuje y pierna como patrones frescos.»

**Resultado**: correcto. El sistema frena sin necesidad de que el usuario perciba la acumulación.

---

## Caso 7. Datos incompletos: día sin registro → asunción conservadora declarada

**Situación**: anteayer no hay registro. El patrón habitual del perfil (3-4 BJJ/semana, normalmente martes) sugiere que pudo haber BJJ.

**Tratamiento** (`docs/12`): se asume **BJJ normal** (agarre 2, core 2, cardio 2, lumbar 1, impacto 1, bisagra 1), marcado como **estimado**. A ×0.6: agarre 1.2, core 1.2, cardio 1.2, lumbar 0.6, impacto 0.6, bisagra 0.6.

**Efecto en la decisión de hoy** (verde, BJJ no): los presupuestos de agarre/core/cardio quedan ligeramente reducidos; la explicación declara: «Anteayer sin registro: asumo BJJ normal por tu patrón habitual (estimado, confianza media). Si no entrenaste, dímelo y recalculo.»

**Resultado**: correcto. La incertidumbre se representa, se actúa de forma conservadora y se ofrece corrección (D6).

---

## Caso 8. Semana simulada completa

Semana tipo con BJJ lunes, miércoles y viernes (normales salvo miércoles duro):

| Día | Estado | Carga relevante (previa) | Decisión | Regla clave |
|---|---|---|---|---|
| Lun | verde, BJJ normal tarde | fin de semana descansado | A (empuje + pierna) | D3 |
| Mar | verde, sin BJJ | todo baja | B (caso 1) | C6 |
| Mié | verde, BJJ duro tarde | bisagra 3, lumbar 2, agarre 4 (del mar) | A reducida, sin bisagra (D5), sin lumbar (D3) | D3, D5 |
| Jue | amarillo, sin BJJ | total alta (doble estímulo mié) | C: cinta 30 min + movilidad | C3, C4 |
| Vie | verde, BJJ normal tarde | carga decaída del mié (×0.6), jue de recuperación | A (empuje + core) | D3 |
| Sáb | verde, sin BJJ | agarre baja (decaída tras el jueves de recuperación) | D técnica: escalera + conos + shadow | P1 (agilidad >7 días) |
| Dom | — | — | descanso | — |

**Observaciones de la semana**:

- Ningún día requiere preguntar al usuario sobre carga acumulada.
- El jueves demuestra el valor del sistema: sin él, un día amarillo tras BJJ duro se habría convertido en sesión potente «porque toca».
- P1 detecta el sábado que la agilidad lleva más de 7 días sin estímulo y la prioriza en un día compatible.

**Resultado**: correcto. La semana cierra con 4 sesiones físicas de estímulo, 1 de recuperación, 1 técnica y 3 de BJJ, sin violar D3-D5 en ningún momento.

---

## Caso 9. Propuestas rechazadas o modificadas

- **9a** (ya en `docs/06`): dominadas con presupuesto de agarre 0 → rechazada; el remo TRX (0.5 con dosis baja) tampoco encaja, así que el tirón se declara patrón pendiente para la próxima sesión sin BJJ.
- **9b**: el usuario pide añadir swings a una familia A antes de BJJ duro → rechazado por D3 (impacto lumbar amarillo) y por presupuesto de bisagra; se ofrece press militar KB como trabajo de estímulo compatible.
- **9c**: fatiga de agarre declarada tras BJJ → la dominada estricta de la familia B se sustituye por dominada asistida con goma (regresión documentada en el catálogo), manteniendo el patrón y el objetivo del bloque.

**Resultado**: correcto. Las sustituciones conservan el objetivo de la sesión y nunca empeoran una dimensión crítica.

---

## Caso 10. Intento de bisagra dos días seguidos → D5

**Situación**: ayer familia B con swings (bisagra exigente). Hoy, verde y sin BJJ, el usuario pide peso muerto con kettlebell.

**Motor**: D5 definida operativamente en esta fase (ver incoherencia I2): ayer hubo ejercicio con coste de bisagra `alto` → hoy la bisagra exigente está prohibida. El peso muerto KB (bisagra media) entra solo si el presupuesto lo permite, pero como prioridad cero y con dosis mínima; en la práctica se desaconseja y se ofrece goblet squat o empuje.

**Resultado**: correcto tras la corrección I2.

---

# Incoherencias encontradas y resolución

## I1. Umbral exacto entre media y alta

**Detectada en**: caso 6. Una dimensión con exactamente 8 puntos era ambigua (`4-8 media`, `> 8 alta`) y dejaba presupuesto 0 en una dimensión `media`, lo que contradecía «media = dosificar».

**Resolución**: aclarado en `docs/12`: el valor en el límite pertenece al nivel inferior (8 = media), y un presupuesto < 0.5 puntos convierte la dimensión en restringida aunque esté en media (decisión conservadora).

## I2. «Bisagra exigente» sin definición operativa

**Detectada en**: caso 10. D5 prohibía «dos días consecutivos de bisagra exigente» sin definir qué cuenta como exigente: dos revisores podían decidir distinto.

**Resolución**: definida en `docs/03` (D5): bisagra exigente = ejercicio con coste de bisagra `alto` ese día, o carga de bisagra acumulada resultante de nivel `media` o superior.

## I3. BJJ técnico el mismo día que sesión física

**Detectada en**: caso 8 (lunes). D4 contaba «física + BJJ duro» como estímulo lumbar, pero no decía nada del BJJ técnico.

**Resolución**: sin cambio normativo: la tabla de `docs/12` asigna lumbar 0 al BJJ técnico, así que no computa como estímulo lumbar. Se confirma como comportamiento esperado, no como hueco.

## I4. Familia A prohíbe agarre medio/alto de forma categórica

**Detectada en**: caso 4. La plantilla A prohibía el agarre medio/alto incluso cuando el presupuesto de agarre era amplio (sin BJJ reciente).

**Resolución**: se acepta como decisión conservadora deliberada (la familia A existe para proteger el BJJ posterior, que siempre carga el agarre). Queda marcada como valor provisional a revisar en la calibración de la Fase 9.

---

# Conclusiones de la validación

- Los escenarios principales (A, B, C, D) producen sesiones coherentes y completas con la biblioteca actual.
- Las reglas duras se aplican siempre antes que la carga y la preferencia; la motivación no anula restricciones.
- No aparecen preguntas que el historial debería responder: bisagra, agarre, tirón y acumulación se infieren.
- Todas las decisiones producen una explicación con reglas citadas e incertidumbre declarada.
- Las dos incoherencias normativas encontradas (I1, I2) están corregidas en los documentos.
- Valores pendientes de calibración con uso real: todos los numéricos (provisionales en `docs/03`, `docs/06`, `docs/12`) más el comportamiento de I4.

## Estado de la Fase 6

Cerrada en su primera versión. Próximo paso según el roadmap: Fase 7, definición del MVP.
