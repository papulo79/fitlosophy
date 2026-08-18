## Propósito

Definir una vía conservadora y trazable para estudiar ejercicios sugeridos por fuentes externas —vídeos, artículos, profesionales o listas— sin convertir una recomendación en una regla del sistema.

Un LLM puede extraer, ordenar y contrastar información; no certifica seguridad clínica ni puede aprobar por sí solo un ejercicio para el motor. La incorporación a `data/ejercicios.yaml` siempre requiere revisión humana explícita.

## Separación de bibliotecas

- `data/ejercicios.yaml` es la **biblioteca estable**. Es la única que leen el motor, el generador y la aplicación.
- `data/candidatos.yaml` es un registro de investigación. Una entrada aquí no es elegible, no aporta carga y no puede aparecer en una propuesta.
- Las fuentes y dossiers se guardan como resúmenes propios y enlaces, no como transcripciones completas ni datos de salud personales. Una fuente se identifica por URL o referencia, fecha de consulta y fragmento breve que justifique la propuesta.

Estados permitidos, en este orden:

| Estado | Significado | Puede usarlo el generador |
|---|---|---|
| `pendiente_de_evidencia` | Se detectó la propuesta, pero falta información crítica. | No |
| `candidato` | Hay un dossier suficiente para revisión, no para entrenar. | No |
| `experimental` | El revisor humano autorizó una prueba controlada. | No |
| `descartado` | No aporta valor, duplica el catálogo o no se puede catalogar con prudencia. | No |

Un ejercicio solo pasa a la biblioteca estable mediante un cambio separado y revisado de `data/ejercicios.yaml`. No existe una transición automática desde este fichero.

## Flujo obligatorio

1. **Registrar la fuente.** Conservar el enlace o referencia, el tipo de fuente, la fecha y un fragmento corto. Si la entrada es una transcripción, distinguir literalmente lo que dice la fuente de las inferencias del agente.
2. **Extraer propuestas.** El analista identifica uno o varios ejercicios, sus aliases y la parte de la fuente que los sostiene. No inventa ejercicios implícitos.
3. **Descartar duplicados.** Comparar por `id`, nombre, aliases, patrón, material y mecánica contra la biblioteca estable. Una variante cosmética no justifica un candidato nuevo; se anota el ejercicio estable equivalente y se descarta.
4. **Investigar y catalogar provisionalmente.** Completar un dossier por ejercicio: ejecución, objetivo, contraindicaciones o límites, material, patrón, coste por dimensión, impacto lumbar, compatibilidad BJJ, dosis inicial y sustitutos. Cada afirmación crítica debe llevar fuente o marcarse como incertidumbre.
5. **Aplicar la puerta de evidencia.** Si falta una ejecución clara, un límite de seguridad relevante, una clasificación lumbar conservadora o una dosis inicial prudente, el estado es `pendiente_de_evidencia` o `descartado`; nunca `candidato`.
6. **Revisión independiente.** El revisor comprueba trazabilidad, deduplicación, coherencia con `docs/05`, `docs/06` y `docs/12`, y que no se haya relajado una restricción lumbar. Decide descartar, mantener pendiente, autorizar prueba experimental o preparar una propuesta para la biblioteca estable.
7. **Validación determinista antes de estable.** La entrada propuesta se pasa por `app/backend/scripts/validar_ejercicio.py`, con `--confirmo-verde` únicamente si la revisión humana acepta de forma expresa esa etiqueta. Después se ejecuta la suite completa.

El analista y el revisor usan respectivamente `docs/roles/analista-candidatos.md` y `docs/roles/revisor-candidatos.md`.

## Dossier mínimo de un candidato

Cada entrada no descartada debe contener, como mínimo:

- Identificador provisional en kebab-case, nombre en español y aliases.
- Fuente(s), fecha de consulta, tipo y fragmento breve relevante.
- Ejecución resumida y límite técnico o de seguridad.
- Motivo por el que aporta algo frente al catálogo y comparación con sus equivalentes.
- Catalogación provisional: patrón principal/secundarios, material, nivel, lateralidad, objetivos, prescripción inicial, coste por dimensiones, impacto lumbar y compatibilidad BJJ.
- Evidencia o incertidumbre explícita para cada campo de seguridad y carga.
- Decisión, autor, fecha y motivo de la última revisión.

No se completa un campo mediante una suposición silenciosa. «No consta» es un resultado válido y bloquea el ascenso a `candidato` cuando el campo es crítico.

## Forma del registro

El agente propone entradas con esta forma. Es una plantilla de investigación: `catalogacion_provisional` no se copia directamente al catálogo estable.

```yaml
- id: dead-bug-variacion          # kebab-case en inglés, provisional o definitivo
  nombre: Variación de dead bug   # español
  aliases: [dead bug]
  estado: pendiente_de_evidencia
  fuentes:
    - tipo: video
      referencia: https://ejemplo.invalid/fuente
      fecha_consulta: 2026-08-18
      fragmento: Resumen breve de la propuesta; no una transcripción completa.
  deduplicacion:
    resultado: no_equivalente     # equivalente | no_equivalente | incierto
    equivalentes_catalogo: []
    justificacion: Qué mecánica o función lo distingue.
  dossier:
    ejecucion: Instrucción resumida y verificable.
    limite_seguridad: Qué obliga a detener o regresionar.
    aporta: Carencia concreta que cubriría frente al catálogo estable.
    catalogacion_provisional:
      patron: core_antiextension
      material: [tatami]
      nivel: base
      lateralidad: bilateral
      coste_dimensiones: {core: bajo}
      impacto_lumbar: amarillo
      compatibilidad_bjj: limitada
      objetivos: [core]
      prescripcion: {series: [2, 3], repeticiones: [5, 8]}
    evidencia:
      ejecucion: confirmado_por_fuente
      limite_seguridad: no_consta
      impacto_lumbar: inferido_conservadoramente
      coste_dimensiones: inferido_conservadoramente
      prescripcion: no_consta
  decision:
    propuesta: pendiente_de_evidencia
    motivo: Falta una fuente suficiente para la dosis inicial y el límite lumbar.
    autor: analista
    fecha: 2026-08-18
```

Los únicos valores de `evidencia` son `confirmado_por_fuente`, `inferido_conservadoramente` y `no_consta`. Una evidencia `no_consta` en ejecución, límite de seguridad, impacto lumbar, coste relevante o prescripción bloquea los estados `candidato` y `experimental`.

## Prueba experimental

La prueba solo existe para reducir incertidumbre de ejecución y tolerancia individual; no demuestra que el ejercicio sea seguro en general ni recalibra por sí sola el modelo de carga.

Condiciones mínimas:

- Recuperación verde, sin dolor lumbar o articular activo que limite el movimiento.
- No hay BJJ normal ni duro el mismo día. Un candidato con impacto lumbar `rojo`, componente explosivo o técnica compleja requiere además **día sin BJJ**, incluido BJJ técnico.
- Una sola novedad experimental por sesión, en dosis inicial conservadora, sin sustituir una intervención de recuperación necesaria.
- No hay otro estímulo lumbar alto el mismo día y se mantienen las reglas de `docs/03`, `docs/04` y `docs/06`.
- Se registra lo ejecutado, RPE, calidad técnica, molestias durante/después y respuesta del día siguiente. Ante dolor, deterioro técnico o duda razonable, se detiene y el resultado vuelve a revisión.

Mientras no exista soporte específico en la aplicación, una prueba se prepara y registra manualmente; no se añade al generador como atajo.

## Uso con Telegram y GitHub

Telegram puede ser una interfaz de entrada: recibe una fuente y devuelve el resumen del analista. No conserva por sí solo el estado canónico ni escribe la biblioteca estable.

El repositorio es la fuente de verdad: guarda los guardarraíles, el registro de candidatos y los dossiers. Un agente solo puede crear una propuesta revisable —issue, rama o PR—; no confirma cambios en `ejercicios.yaml`, no modifica reglas del motor y no recibe perfiles, historiales ni molestias personales de los usuarios.

## Criterios de descarte inmediato

- Es idéntico o sustancialmente equivalente a un ejercicio estable sin aportar una diferencia relevante.
- Requiere material no disponible o una adaptación no descrita con suficiente precisión.
- La fuente no permite reconstruir una ejecución razonablemente segura.
- No se puede estimar conservadoramente el impacto lumbar o el coste relevante.
- Promete diagnóstico, tratamiento o prevención de lesiones sin base suficiente, o contradice una restricción vigente del sistema.
- La fuente presenta señales de riesgo que el dossier no puede resolver mediante una regresión o dosis prudente.
