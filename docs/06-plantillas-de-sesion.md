# Generador de sesiones

## Propósito

Definir cómo se construye una sesión concreta una vez que el motor (`docs/03`) ha seleccionado la familia de sesión, el presupuesto por dimensión y los patrones prioritarios y restringidos. Corresponde a la Fase 5 del roadmap (`docs/10`).

Todos los valores numéricos son provisionales; se calibran en la Fase 9.

## Bloques de una sesión

Toda sesión se compone de bloques ordenados (`docs/11`):

- **B0 · Calentamiento** (5-10 min): movilidad, activación y coordinación. Ejercicios de coste bajo, `impacto_lumbar` verde (dead bug, puente de glúteos, escalera de agilidad).
- **B1 · Principal**: fuerza o potencia. 2-4 ejercicios según familia. Los ejercicios explosivos van primero, la fuerza después.
- **B2 · Accesorio y core**: 1-3 ejercicios de estabilidad o trabajo complementario.
- **B3 · Acondicionamiento** (opcional): solo en familias que lo permiten y si queda presupuesto de cardio.
- **B4 · Vuelta a la calma** (opcional, 3-5 min): respiración y movilidad suave.

## Plantillas por familia

### A. Físico compatible con BJJ

- Duración: 20-35 min. RPE objetivo: 5-6. Sin fallo muscular.
- Bloques: B0 + B1 (2-3 ejercicios) + B2 (1-2 ejercicios).
- Patrones permitidos: empuje, dominante de rodilla, core (variantes anti-), tirón con coste de agarre bajo, acondicionamiento suave.
- Prohibidos: `impacto_lumbar` amarillo o rojo (regla D3), ejercicios explosivos, coste de agarre medio o alto.
- Debe quedar margen claro para un BJJ normal o duro posterior.

### B. Físico potente sin BJJ

- Duración: 40-60 min. RPE objetivo: 7-8.
- Bloques: B0 + B1 (3-4 ejercicios) + B2 (2 ejercicios) + B3 opcional.
- Permite fuerza, potencia y acondicionamiento específico.
- Puede incluir ejercicios de `impacto_lumbar` amarillo o rojo solo si la recuperación es verde, con un máximo de un estímulo lumbar alto en el día (regla D4).

### C. Recuperación activa

- Duración: 20-45 min. RPE objetivo: 2-4.
- Bloques: movimiento continuo + B2 ligero. Sin B1.
- Patrones: `recuperacion`, movilidad, core verde en dosis baja.
- Ningún ejercicio puede superar coste bajo en ninguna dimensión.
- La sesión debe dejar mejores sensaciones que al comenzar; si no, se recorta.

### D. Técnica y agilidad

- Duración: 15-30 min. Intensidad modulable según exista BJJ posterior.
- Bloques: B0 + trabajo técnico (escalera, conos, desplazamientos, shadow grappling, comba técnica).
- Puede sustituir a la familia A cuando el objetivo del día es técnica, o añadirse como bloque corto a otra familia si el presupuesto lo permite.

## Reglas de composición

1. Un patrón principal solo puede aparecer una vez por sesión. Los patrones secundarios no cuentan para esta regla, pero dos ejercicios no pueden compartir el mismo secundario.
2. Los patrones prioritarios del motor entran primero en B1; si no caben en el presupuesto, se anotan para la siguiente sesión.
3. Máximo un ejercicio de `impacto_lumbar` rojo por día, solo en familia B, y ese día no puede haber ningún otro ejercicio amarillo ni BJJ duro (D4).
4. Los ejercicios unilaterales cuentan su dosis por lado y van después de los bilaterales dentro del mismo bloque.
5. Todo ejercicio seleccionado debe tener al menos un sustituto o una regresión disponible en el catálogo, o ser prescindible sin invalidar la sesión.
6. Ningún ejercicio restringido por el motor puede entrar, ni siquiera como sustituto.
7. La duración estimada de la sesión no puede superar `tiempo_disponible`; si lo supera, se recorta en este orden: B3, B2, reducir series de B1 al mínimo del rango, eliminar el último ejercicio de B1.
8. B0 y B4 no computan en el presupuesto de carga: su dosis es mínima y su función es preparatoria, no de estímulo.
9. Filtro de material: solo entran ejercicios cuyo material requerido (salvo tatami, que cuenta como suelo) esté en `material_disponible`. Los ejercicios con `sin_material: true` entran siempre, incluso con la lista vacía. Si un patrón prioritario queda sin ejercicios disponibles (tirón sin barra, TRX ni gomas, por ejemplo), se declara en la explicación como patrón pendiente y se retoma cuando haya material.

## Reglas de dosificación

Se usan los rangos de `prescripcion` del catálogo:

| Familia | Series | Repeticiones | Reserva (reps en recámara) |
|---|---|---|---|
| A | extremo bajo del rango | extremo bajo | 3-5 |
| B | rango medio-alto | rango medio | 1-3 |
| C | por debajo del rango o mínimo | mínimo | sin estímulo |
| D | según técnica | según técnica | sin estímulo |

- Los flags del catálogo se respetan siempre: `evitar_fallo`, `detener_si_falla_tecnica`, `sin_balanceo`.
- Dosis en el extremo bajo del rango (familias A y C): los puntos del ejercicio se reducen a la mitad en las dimensiones donde su coste es `bajo`. Las dimensiones con coste medio o alto computan íntegras.
- Descansos provisionales: fuerza 2-3 min; accesorio y core 60-90 s; acondicionamiento por densidad, sin recuperación completa.
- La progresión entre semanas sigue `docs/07`: una sola variable a la vez, y solo si todas las series se completaron en el extremo alto con el RPE previsto o menor.

## Reglas de sustitución

El usuario puede cambiar cualquier ejercicio sin invalidar la sesión si se cumple:

1. El sustituto pertenece al mismo patrón principal y cumple el mismo objetivo en el bloque.
2. Su `impacto_lumbar` no es de un color superior al original.
3. No empeora ninguna dimensión cuyo presupuesto esté en 0 o 1 punto.
4. No está restringido por el motor ni viola D3-D5.

Orden de búsqueda del sustituto: campo `sustitutos` del catálogo → misma familia de progresión/regresión → cualquier ejercicio del patrón que cumpla 1-4.

## Validación final de la sesión

Antes de proponer la sesión se verifica:

```text
para cada dimensión:
    puntos_sesión = suma de puntos de coste (bajo=1, medio=2, alto=3;
                    secundarios a la mitad) de todos los ejercicios
    exigir: puntos_sesión <= presupuesto de la dimensión
exigir: duración estimada <= tiempo_disponible (si se declaró)
exigir: reglas D3, D4, D5 verificadas sobre la selección final
exigir: ningún patrón principal repetido
exigir: cada bloque tiene una justificación que pueda mostrarse al usuario
```

Si la validación falla, se sustituye el ejercicio conflictivo por uno de menor coste en la dimensión afectada; si no hay alternativa, se elimina el ejercicio y se anota en la explicación.

## Ejemplo completo

Escenario: recuperación verde, sin dolor, BJJ normal por la tarde. Ayer: swing a una mano + peso muerto + BJJ normal → carga activa: agarre 8 (media), lumbar 6 (media), bisagra 6 (media), core 4.5 (media) (ejemplo de `docs/12`).

Motor: familia A. Presupuestos (umbral alto 8 − carga activa, factor compatible 0.5):

```text
lumbar:   (8-6) * 0.5 = 1
bisagra:  (8-6) * 0.5 = 1
agarre:   (8-8) * 0.5 = 0
empuje:   (8-0) * 0.5 = 4
rodilla:  (8-0) * 0.5 = 4
core:     (8-4.5) * 0.5 = 1.75
```

Sesión generada (dosis al extremo bajo del rango, familia A: coste bajo computa la mitad; B0 no computa):

```text
B0: dead bug 2×6 por lado + escalera de agilidad 4 pasadas   # no computa
B1: flexión clásica 3×12 (empuje 0.5, core 0.5)
    goblet squat 3×10 (rodilla 2, core 0.5)
B2: pallof press 3×10 por lado (core 0.5)
```

Validación: lumbar 0 ≤ 1; bisagra 0 ≤ 1; agarre 0 ≤ 0; empuje 0.5 ≤ 4; rodilla 2 ≤ 4; core 1.5 ≤ 1.75 → sesión válida.

Ejemplo de rechazo: si el usuario pide cambiar la flexión por dominadas (agarre 2 > presupuesto 0), se rechaza la sustitución. El remo en TRX (agarre 0.5 con dosis baja) tampoco encaja: con el agarre en el límite no cabe ningún tirón hoy y el patrón se declara pendiente para la próxima sesión sin BJJ.

Explicación mostrada: «Familia A por BJJ normal esta tarde. Bisagra y agarre restringidos por la sesión de ayer: sin swings, pesos muertos ni dominadas (D3, C1). Empuje y pierna como patrones frescos prioritarios. Core dosificado al mínimo por carga media acumulada.»

## Valores provisionales

- Duraciones y RPE de las plantillas.
- Reservas de repeticiones por familia y descansos.
- Reducción a la mitad del coste bajo con dosis mínima.
- Exclusión de B0 y B4 del presupuesto.
- Umbral de presupuesto crítico en sustituciones (1 punto).
- Orden de recorte por falta de tiempo.
