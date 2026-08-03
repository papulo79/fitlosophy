# Modelo de carga e inferencia

## Propósito

Definir cómo el historial y la biblioteca se transforman en carga activa por dimensiones: qué sigue fatigado, cuánto y con qué confianza. Es la entrada que el motor de decisión (`docs/03`) convierte en familia de sesión y presupuesto.

Corresponde a la Fase 3 del roadmap (`docs/10`). Todos los valores numéricos de este documento son **provisionales**: se calibran con uso real (Fase 9).

## Dimensiones de carga

Lista definitiva. La carga nunca se reduce a un único valor global (`docs/11`).

- `lumbar`: demanda sobre la zona lumbosacra. Dimensión protegida por las reglas de seguridad.
- `bisagra`: trabajo de bisagra de cadera y cadena posterior.
- `rodilla_piernas`: demanda de cuádriceps, rodilla y piernas en general.
- `empuje`: trabajo de empuje (horizontal y vertical).
- `tiron`: trabajo de tracción (horizontal y vertical).
- `agarre`: fatiga de antebrazo y mano. Clave por el BJJ.
- `core`: trabajo de estabilización en todas sus variantes.
- `cardio`: demanda cardiovascular.
- `impacto_articular`: estrés por impacto y cambios de dirección (saltos, agilidad, caídas en BJJ).

La dimensión `total` no se asigna directamente: se deriva de la combinación de las demás y representa la fatiga sistémica.

Cada patrón de movimiento alimenta dimensiones concretas (mapeo en `docs/05`). Cada ejercicio declarará su coste base por dimensión cuando se amplíe la biblioteca (Fase 2, pendiente).

## Niveles

Cada dimensión se expresa en tres niveles, coherente con el vocabulario de `coste` e `impacto_lumbar`:

- `baja`: sin restricción.
- `media`: dosificar; el patrón asociado pierde prioridad.
- `alta`: restringir; solo dosis reducidas o exclusión temporal.

## Ventanas temporales y decaimiento

La carga activa de una sesión decae con el tiempo (factores provisionales):

```text
últimas 24 h  → 100 % de la carga
24 - 48 h     → 60 %
48 - 72 h     → 30 %
más de 72 h   → despreciable
```

Excepción: una respuesta negativa registrada (molestia posterior, mal estado al día siguiente) mantiene la dimensión afectada al nivel actual durante una ventana adicional de 24 h.

## Puntuación provisional

Para que dos personas lleguen a la misma conclusión con las mismas reglas, la carga se calcula con puntos:

- Coste base por dimensión: `bajo` = 1, `medio` = 2, `alto` = 3.
- Patrón secundario: la mitad de puntos en las dimensiones que alimenta.
- Ajustes de dosis (multiplicadores sobre los puntos del ejercicio):
  - Volumen dentro del rango prescrito: ×1.0
  - Volumen por encima del rango: ×1.25
  - Trabajo al fallo o RPE real ≥ 9: ×1.25
  - RPE real ≤ 5: ×0.75
  - Fatiga previa alta en la misma dimensión: ×1.25
- Umbrales por dimensión y ventana: < 4 puntos = `baja`, 4-8 = `media`, > 8 = `alta`. Un valor exactamente en el límite pertenece al nivel inferior (8 = `media`).
- Presupuesto crítico: si el presupuesto de una dimensión (umbral alto − carga activa) queda por debajo de 0.5 puntos, la dimensión se trata como restringida aunque su nivel sea `media` (decisión conservadora).

## Carga estimada del BJJ

El BJJ no detalla ejercicios, así que su carga es **estimada**, no observada. Puntos provisionales según clasificación y duración de referencia (75 min):

| Dimensión | Técnico | Normal | Duro |
|---|---|---|---|
| agarre | 1 | 2 | 3 |
| core | 1 | 2 | 3 |
| cardio | 1 | 2 | 3 |
| lumbar | 0 | 1 | 2 |
| impacto_articular | 0 | 1 | 2 |
| bisagra | 0 | 1 | 1 |

Ajustes: duración muy superior a la referencia, ×1.25; fatiga de agarre declarada, +1 en `agarre`. Una sesión de BJJ se trata como una sesión más a efectos de acumulación y decaimiento.

## Reglas de acumulación

1. La carga activa de una dimensión es la suma de los puntos decaídos de todas las sesiones (físicas y BJJ) dentro de la ventana de 72 h.
2. Doble sesión: ambas sesiones suman sin multiplicador adicional, pero si dos sesiones del mismo día dejan una dimensión en nivel `alto`, el día siguiente se trata como conservador en esa dimensión aunque los puntos decaigan.
3. La dimensión `total` es `alta` si hay dos o más dimensiones en `alta`, o tres o más en `media`.
4. Una sesión de recuperación (patrón `recuperacion`) no suma carga en ninguna dimensión.

## Reglas de inferencia de patrones

- El sistema registra el tiempo desde el último estímulo de cada patrón. Una ausencia superior a 7 días convierte el patrón en candidato prioritario si el presupuesto lo permite.
- Un patrón estimulado dos días consecutivos con carga `media` o `alta` queda restringido al día siguiente.
- La bisagra tiene regla dura adicional (`docs/04`): nunca dos días consecutivos de bisagra exigente.

## Tratamiento de datos incompletos

Coherente con `docs/09` (dato conocido, estimado, desconocido):

- Sesión física sin RPE registrado: se calcula con los multiplicadores neutros y se marca como estimada.
- Día sin registro: carga desconocida. Si el patrón de uso sugiere que pudo haber sesión, se asume carga `media` en las dimensiones probables y se declara la incertidumbre en la explicación.
- BJJ posible pero no confirmado: se asume `normal` y se conserva margen (regla de `docs/03`).
- Nunca se inventan datos: la incertidumbre se representa y se actúa de forma conservadora.

## Ejemplo completo (pseudocódigo)

Historial de las últimas 48 h:

```text
ayer:
  - swing a una mano (dominante_cadera + core_antirotacion, coste alto, volumen en rango)
  - peso muerto maleta (dominante_cadera, coste medio, volumen en rango)
  - remo unilateral con apoyo (tiron_horizontal + core_antirotacion, coste medio)
  - BJJ normal, 75 min
hoy: decisión de sesión
```

Cálculo (ventana 24 h, factor 1.0):

```text
swing una mano:  bisagra 3, lumbar 3, agarre 3, core 1.5 (secundario)
peso muerto:     bisagra 2, lumbar 2, agarre 1
remo:            tiron 2, agarre 2, core 1 (secundario)
BJJ normal:      agarre 2, core 2, cardio 2, lumbar 1, impacto 1, bisagra 1
─────────────────────────────────────────────────────────
carga activa:    agarre 8 (media), bisagra 6 (media), lumbar 6 (media),
                 core 4.5 (media), tiron 2 (baja), cardio 2 (baja),
                 impacto 1 (baja)
```

Consecuencias funcionales:

- Cuatro dimensiones en `media` → `total` = `alta`.
- Lumbar y bisagra en `media` → excluir swings, windmills y pesos muertos de la sesión de hoy.
- Agarre en 8 → presupuesto 0: dimensión restringida (regla de presupuesto crítico). Sin dominadas, remos ni trabajo de agarre hoy; el tirón se declara patrón pendiente.
- Si hoy hay BJJ normal o duro → familia A (compatible) con énfasis en empuje, que está `baja`.
- La explicación mostrará: «lumbar y bisarga cargadas por swing + peso muerto + BJJ de ayer; agarre al límite; empuje y piernas frescas».

El usuario no ha declarado nada sobre bisagra ni agarre: el sistema lo infiere (`docs/09`).

## Valores provisionales

- Factores de decaimiento (100/60/30 %).
- Puntos por nivel de coste (1/2/3) y multiplicadores de dosis.
- Umbrales de niveles (4/8).
- Tabla de carga estimada del BJJ y duración de referencia (75 min).
- Regla de dimensión `total` (2 altas o 3 medias).
- Umbral de ausencia de patrón (7 días).

Estos valores se calibran en la Fase 9 comparando la carga estimada con la respuesta real registrada.
