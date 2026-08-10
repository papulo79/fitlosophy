# Prompt: proponer un ejercicio nuevo para el catálogo

Prompt para pegar en un agente externo (Claude, Kimi, ChatGPT…) junto con una transcripción de vídeo o un artículo, para que devuelva un ejercicio con la forma que espera `data/ejercicios.yaml`.

Vive en el repositorio a propósito: los vocabularios de abajo son copia de la sección `valores` del catálogo y del inventario de `data/perfil.yaml`. Si se amplía un dominio, este documento se actualiza en el mismo commit — `tests/test_prompt_ejercicio.py` falla si se desincronizan.

Lo que devuelva el agente **no se pega directamente**: se pasa por el validador, que comprueba de forma determinista todo lo comprobable.

```bash
cd app/backend
./.venv/bin/python scripts/validar_ejercicio.py propuesta.yaml
```

---

## El prompt

> Eres un asistente que propone entradas para el catálogo de ejercicios de un sistema personal de entrenamiento. Te doy una fuente (transcripción de vídeo o artículo) y quiero **un único ejercicio** extraído de ella, en YAML, con el contrato exacto que te indico.
>
> ### Sobre el atleta
>
> Practicante de jiu-jitsu brasileño (cinturón azul, 3-4 sesiones por semana de intensidad normal a dura), que entrena fuerza y acondicionamiento en un garaje. **Tiene episodios lumbares recientes**: la carga lumbar es la restricción de seguridad dominante del sistema. Entrena en casa; no hay barra olímpica, discos, máquinas ni mancuernas.
>
> ### Vocabularios cerrados — no inventes valores
>
> `patron` (uno solo, el principal):
> `empuje_horizontal`, `empuje_vertical`, `tiron_horizontal`, `tiron_vertical`, `dominante_rodilla`, `dominante_cadera`, `core_antiextension`, `core_antirotacion`, `core_lateral`, `core_flexion_cadera`, `core_rotacion`, `acondicionamiento`, `agilidad`, `movilidad_cargada`, `recuperacion`
>
> `dimensiones` (claves de `coste_dimensiones`):
> `lumbar`, `bisagra`, `rodilla_piernas`, `empuje`, `tiron`, `agarre`, `core`, `cardio`, `impacto_articular`
>
> `nivel_coste` (valores de `coste_dimensiones`): `bajo`, `medio`, `alto`
> `impacto_lumbar`: `verde`, `amarillo`, `rojo`
> `compatibilidad_bjj`: `si`, `limitada`, `no`
> `nivel`: `base`, `intermedio`, `avanzado`
> `lateralidad`: `bilateral`, `unilateral`
>
> `material` disponible (usa solo estos tokens; lista vacía si no hace falta nada):
> `trx`, `tatami`, `barra_dominadas`, `kettlebell` (8, 12 y 16 kg), `comba`, `caja`, `goma`, `conos`, `escalera_agilidad`, `cinta`
>
> ### Contrato de campos
>
> ```yaml
> - id: kebab-case-en-ingles          # obligatorio, único
>   nombre: Nombre en español          # obligatorio
>   descripcion: >-                    # obligatorio, 1-2 frases
>     Ejecución en imperativo y la clave técnica que más importa en este perfil.
>     No repitas el nombre del ejercicio ni la dosis.
>   patron: dominante_cadera           # obligatorio, del vocabulario
>   secundarios: [core_antirotacion]   # opcional, del mismo vocabulario
>   material: [kettlebell]             # obligatorio (puede ir vacío)
>   sin_material: false                # opcional; true si se puede hacer sin nada
>   nivel: intermedio                  # obligatorio
>   lateralidad: bilateral             # obligatorio
>   explosivo: false                   # opcional
>   isometrico: false                  # opcional
>   coste_dimensiones:                 # obligatorio, ver aviso abajo
>     bisagra: alto
>     lumbar: medio
>   impacto_lumbar: amarillo           # obligatorio, ver aviso abajo
>   compatibilidad_bjj: limitada       # obligatorio
>   objetivos: [potencia]              # obligatorio; el primero define la intención mostrada
>   prescripcion:                      # obligatorio
>     series: [3, 5]                   # rangos de dos elementos crecientes
>     repeticiones: [8, 12]
>     por_lado: false                  # opcional
> ```
>
> ### Reglas
>
> 1. **Todo el texto visible en español.** Solo el `id` va en inglés.
> 2. **`impacto_lumbar` y `coste_dimensiones` alimentan directamente el motor de decisión**: determinan si el ejercicio puede programarse antes de una sesión de jiu-jitsu o en un día de mala recuperación. Propónlos **con una justificación de una línea cada uno**, fuera del YAML. Ante la duda, sé conservador: **nunca propongas `impacto_lumbar: verde`**; el mínimo que puedes proponer es `amarillo`, y quien revisa decidirá si baja.
> 3. Si el ejercicio tiene `impacto_lumbar: rojo` o requiere cuidado técnico, **la descripción debe decirlo con palabras**, no solo con la etiqueta.
> 4. Si la fuente no da información suficiente para un campo, **dilo explícitamente en vez de inventarlo**.
> 5. No propongas ejercicios que requieran material que no esté en la lista.
> 6. `objetivos` se lista por orden de importancia: el primero decide qué intención se le muestra al atleta.
>
> ### Salida
>
> Primero el bloque YAML dentro de un bloque de código, y después estas dos líneas:
>
> ```
> impacto_lumbar: <valor> — <justificación en una línea>
> coste_dimensiones: <justificación en una línea de las dimensiones elegidas>
> ```
>
> Nada más: sin introducción ni resumen.
>
> ### Fuente
>
> [pega aquí la transcripción o el artículo]

---

## Después

1. Guarda el YAML en un fichero, por ejemplo `propuesta.yaml`.
2. Valídalo: `./.venv/bin/python scripts/validar_ejercicio.py propuesta.yaml`. Comprueba dominios, referencias, unicidad y coherencia, e imprime **qué cubre ya el catálogo en ese patrón** para poder decidir si aporta algo.
3. Decide con criterio lo único que no es mecánico: si aporta cobertura nueva, si el impacto lumbar es correcto para este atleta y si los costes por dimensión son plausibles.
4. Pega el bloque en `data/ejercicios.yaml` y ejecuta la suite: `./.venv/bin/python -m pytest`.
