# WODs y acondicionamiento estructurado

## Propósito

Definir cómo se integran los WOD (workouts metabólicos de formato cerrado, en la línea de CrossFit) como una **variante de dosificación del bloque B3 · Acondicionamiento** (`docs/06`), bajo demanda del atleta: entrenamientos algo más intensos a nivel cardiovascular sin descuidar el resto del modelo. Corresponde a la Fase 9 (`docs/10`): ampliación del modelo documentada antes de construirse.

Todos los valores numéricos son provisionales; se calibran en la Fase 9.

## Qué es un WOD en este sistema

Un WOD es un bloque corto de trabajo metabólico con **estructura temporal cerrada**: el tiempo o el trabajo se fija por diseño y el atleta compite contra el reloj o contra sus propias rondas. No es una familia de sesión nueva ni un entrenamiento aislado: es la forma que puede tomar el bloque B3 dentro de una sesión ya decidida por el motor (`docs/03`).

El formato no cambia qué se entrena; cambia cómo se dosifica el acondicionamiento. La decisión de *si* toca cardio, con qué presupuesto y en qué familia sigue siendo enteramente del motor.

## Objetivos y dominio de tiempo

Cada formato apunta a una adaptación concreta; mezclarlos en un mismo WOD anula el objetivo:

| Objetivo | Dominio de tiempo | Sistema energético | Formato natural |
|---|---|---|---|
| Capacidad aeróbica («motor») | 12-30 min | Oxidativo | AMRAP largo, EMOM largo |
| Umbral y potencia metabólica | 3-10 min | Glucolítico | *For time* |
| Recuperación entre esfuerzos | cualquiera | Mixto | EMOM (descanso estructurado) |

La prioridad del atleta es el primer objetivo: capacidad de sostener esfuerzo, transferible al BJJ y coherente con la filosofía del sistema (`docs/02`: estímulo, no destrucción). Los WOD cortos e intensos (*for time*) son la excepción, no la norma.

## Formatos

- **AMRAP** (*as many rounds as possible*): tiempo fijo, rondas variables. El atleta sostiene un ritmo constante y submáximo. Es el formato por defecto.
- **EMOM** (*every minute on the minute*): cada minuto empieza una dosis; lo que sobra descansa. El descanso estructurado protege la técnica.
- **Por tiempo** (*for time*): trabajo fijo contra cronómetro. Solo en familia B y con techo de intensidad medio (D4/C4 mandan sobre el cronómetro).
- **Rondas fijas por tiempo** (cortar a los X minutos): variantes de los anteriores.

## Reglas por familia

### A. Compatible con BJJ

- Formatos: AMRAP largo (12-20 min) suave o EMOM (10-14 min).
- RPE del bloque: 5-6; la primera mitad debe sentirse fácil.
- Ejercicios de `impacto_lumbar` verde, sin explosivos, coste de agarre bajo (hereda las prohibiciones de la familia, `docs/06`).
- Con BJJ normal o duro después, el WOD se dosifica para terminar con margen claro.

### B. Potente sin BJJ

- Formatos: AMRAP (8-20 min), EMOM (8-14), *for time* (3-10 min).
- RPE del bloque: 7-8; todavía sin fallo mecánico.
- Puede incluir ejercicios de `impacto_lumbar` amarillo si la recuperación es verde, contando dentro del único estímulo lumbar alto del día (D4).

### C. Recuperación activa

- Sin WOD. El formato cerrado contradice el objetivo de la familia (RPE 2-4).

### D. Técnica y agilidad

- Un EMOM corto (6-10 min) de técnica de apoyos (escalera, conos, comba) es compatible como complemento; el agarre y el lumbar se dosifican igual que en cualquier sesión.

## Selección de ejercicios para un WOD

El WOD se compone de 2-4 movimientos elegidos por el generador con los mismos filtros que cualquier ejercicio (presupuesto, material, regla de variedad, `docs/06`), más estos criterios específicos:

1. **Impacto lumbar verde** (salvo familia B verde, donde un amarillo cabe bajo D4). Los rojos quedan fuera del formato WOD siempre: el fallo de técnica metabólica es precisamente lo que el formato premia cuando el atleta está fatigado.
2. **Alternar grupos musculares**: los movimientos se ordenan para que el músculo que descansa de una estación trabaje en la siguiente, manteniendo movimiento continuo.
3. **Agarre dosificado**: máximo un movimiento con coste de agarre distinto de bajo, y nunca como cuello de botella (el fallo de agarre detiene el WOD entero).
4. **Sin fallo programado**: los rangos se escogen para que el atleta con margen de la familia pueda moverse casi sin parar. Si una estación exige paradas largas, la carga o las repeticiones están mal elegidas (escala: bajar carga → bajar repeticiones → modificar rango → cambiar modalidad).
5. **Material y catálogo**: solo ejercicios del catálogo con `prescripcion`; la regla 9 de `docs/06` (filtro de material) aplica igual.
6. **Ejercicios prohibidos en WOD** con el catálogo actual: todos los `impacto_lumbar: rojo` (swing a una mano, windmill, russian twist, lunge-with-twist, kettlebell-alternating-hang-clean), los swings incluso en amarillo (bisagra alta, D5), y todo `core_rotacion`.

## Dosificación y puntuación de carga

- El WOD puntúa como cualquier sesión: los puntos de coste de sus ejercicios (`docs/12`) suman a sus dimensiones con el peso temporal de la sesión. No hay multiplicador de «intensidad de formato»: la dosis ya acota el estímulo.
- La dosis del formato (minutos, rondas, repeticiones por estación) se declara en la propuesta como dosis de B3; las repeticiones por estación se mantienen por debajo del fallo estimado con la reserva de la familia.
- El trabajo real realizado (rondas completadas, RPE real) se registra en el cierre y alimenta la calibración como cualquier sesión.

## Reglas duras aplicables

Las reglas de seguridad (`docs/03`) no se relajan por ser «solo un bloque corto»:

- **D3**: con BJJ normal o duro después, el WOD no incluye `impacto_lumbar` amarillo ni rojo.
- **D4**: el WOD cuenta dentro del único estímulo lumbar alto del día; un WOD amarillo en familia B es incompatible con otro amarillo o rojo en B1/B2.
- **D5**: un WOD con coste de bisagra (p. ej., KB deadlift en volumen) computa para la regla de bisagra exigente: nunca dos días consecutivos.
- **D1/D2/C1-C3**: un día rojo, con dolor relevante o con `total` alta no tiene WOD, igual que hoy no tiene B3.

## Pacing y ejecución

- En AMRAP >10 min, la primera ronda debe sentirse incómodamente lenta: la deriva cardiovascular eleva la FC 10-15 ppm a lo largo del bloque, y salir rápido fuerza el sistema glucolítico y arruina el objetivo oxidativo.
- Regla práctica: la ronda más lenta no más de un 10 % más lenta que la más rápida.
- Se descansa en las transiciones, no de pie quieto: si una estación obliga a 45 s parado, la escala es insuficiente (ver selección, criterio 4).
- Los flags del catálogo mandan dentro del formato: `evitar_fallo`, `detener_si_falla_tecnica`. Fatiga técnica = se detiene o se escala, aunque quede tiempo en el reloj.

## Registro

- **Rondas completadas**: marcador del WOD en AMRAP y por tiempo; se registra en el cierre de la sesión y es el dato que permite comparar el mismo WOD entre semanas. En EMOM no se registra: el formato ya fija los minutos. Se puede corregir desde el historial como cualquier cierre.
- **Pesos**: cada estación es un ítem normal, así que el peso apuntado se guarda por ítem (`carga_kg_real`), también en las estaciones con kettlebell.
- **Export**: `sesiones.csv` incluye `rondas_completadas` y el diario (`historico.md`) la muestra junto al cierre, para el análisis de datos.

## Ejemplos (catálogo actual)

Escenario 1: familia A, BJJ normal por la tarde, todo fresco.

```text
B3 (EMOM 12):  minuto 1: 10 squat-libre + 6 pushup-classic
                minuto 2: 40 s rope-technical
RPE del bloque: 5-6. Sin coste lumbar ni de agarre; cardio dosificado.
```

Escenario 2: familia B verde, sin BJJ, presupuesto amplio.

```text
B3 (AMRAP 15):  10 goblet-squat (12 kg)
                8 pushup-classic
                40 s rope-technical
Objetivo: 6-8 rondas con rondas homogéneas (±10 %).
Puntuación: rodilla_piernas y cardio de las estaciones, según coste de cada ejercicio.
```

Escenario 3: familia B, *for time* puntual (uso excepcional).

```text
B3 (por tiempo):  5 rondas de 8 burpee + 20 m shuttles (cones-shuttle)
Techo: RPE ≤ 8; si la técnica de apoyos se degrada, se detiene.
```

## Disparador y generación

Reglas con las que el generador construye el WOD (implementación provisional, Fase 9):

- **Bajo demanda**: se genera solo si el estado diario declara `preferencia: acondicionamiento` (P2). La pantalla del estado diario lo ofrece como selector visible y cerrado («Cardio»); sin preferencia, el B3 conserva su comportamiento clásico (familia B) o no aparece (familia A).
- **Condiciones**: familia A o B, presupuesto de cardio ≥ 1 punto y al menos 2 estaciones elegibles. Si no se cumplen, no hay WOD y la propuesta lo anota con el motivo.
- **Formato por familia** (provisional): A → EMOM 12 min, RPE 5-6; B → AMRAP 15 min, RPE 7-8. Los dominios de tiempo de la tabla de objetivos son los límites de la validación.
- **Estaciones = ítems normales**: puntúan presupuesto, admiten sustitución validada y comparten la regla 1 de patrones con el resto de la sesión (el WOD se construye antes que B1/B2 y reserva sus patrones: la preferencia del día es el cardio).
- **Dosis de estación** (provisional): parte del extremo bajo de la serie prescrita — ×1.0 en AMRAP (equivale a una serie) y ×0.8 en EMOM, con mínimos de 5 y 4 repeticiones —, nunca series × repeticiones. La estación se repite varias veces por sesión, así que el volumen total lo multiplica el formato por rondas.
- **Recorte por tiempo** (regla 7): el WOD se elimina entero, nunca estación a estación.
- **Persistencia**: la cabecera del formato (tipo, minutos, RPE, instrucción) se guarda en la propuesta; las estaciones viven como ítems de B3, así que una sustitución queda reflejada en ambas.

## Validación

Antes de proponerse, el WOD se verifica como cualquier sesión (`docs/06`): puntos por dimensión dentro del presupuesto, D3-D5 sobre la selección, duración dentro de `tiempo_disponible`. La regla 7 de recorte por tiempo actúa igual: primero B3.

## Fuera de alcance

- Leaderboards, repeticiones máximas, competiciones tipo Open y clasificaciones: el WOD compite contra el reloj del propio atleta, no contra otros.
- WODs con barra, mancuernas pesadas o gimnásticos de alta destreza: fuera del material y del perfil.

## Valores provisionales

- Dominios de tiempo por objetivo (3-10 / 12-30 min).
- RPE de bloque por familia (5-6 en A, 7-8 en B).
- Formato por familia (A → EMOM 12, B → AMRAP 15) y dominios de validación.
- Número de movimientos (2-4; el generador usa 2-3), estación de agarre máxima (1).
- Fórmula de dosis de estación (×1.0 AMRAP / ×0.8 EMOM del extremo bajo; mínimos 5 y 4).
- Umbral de presupuesto de cardio para generar WOD (1 punto).
- Regla de homogeneidad de rondas (±10 %).
- Lista de ejercicios prohibidos en WOD (deriva del catálogo; se revalida al crecer la biblioteca).
